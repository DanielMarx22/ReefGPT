import os
import json
import time
from dateutil.parser import isoparse
from playwright.sync_api import sync_playwright
from supabase import create_client
from datetime import datetime, timezone

supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_KEY", "")
)

def scrape_fusion_for_user(user_id: str, fusion_user: str, fusion_pass: str):
    try:
        print(f"[Scraper] Starting background scrape for user: {user_id}")
        
        # Store intercepted data
        tlog_data = []
        ilog_data = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            apex_id = None

            def handle_response(response):
                nonlocal apex_id, tlog_data, ilog_data
                if response.request.resource_type in ["fetch", "xhr"]:
                    try:
                        if "application/json" in response.headers.get("content-type", ""):
                            body = response.json()
                            
                            # Intercept the Apex ID dynamically
                            if "api/apex" in response.url and isinstance(body, list) and len(body) == 2:
                                apexes = body[1]
                                if len(apexes) > 0:
                                    apex_id = apexes[0].get("_id")
                                    print(f"[Scraper] Discovered Apex ID: {apex_id}")
                                    
                            # Capture tlog (Trident logs)
                            if "tlog" in response.url and isinstance(body, list):
                                print(f"[Scraper] Captured tlog with {len(body)} records.")
                                tlog_data.extend(body)
                                
                            # Capture ilog (Input logs)
                            if "ilog" in response.url and isinstance(body, dict) and "items" in body:
                                items = body.get("items", [])
                                print(f"[Scraper] Captured ilog with {len(items)} items.")
                                ilog_data.extend(items)

                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                page.goto("https://apexfusion.com/login")
                page.fill('#index-login-username', fusion_user)
                page.fill('#index-login-password', fusion_pass)
                page.click('button.btn-primary')
                
                print("[Scraper] Waiting for Apex list to load...")
                try:
                    # The Apex list page contains the text "Serial" for each Apex unit
                    page.wait_for_selector('text="Serial"', timeout=15000)
                    print("[Scraper] Found Apex box. Clicking to open dashboard...")
                    # Click the word "Serial" to trigger the JS navigation to the dashboard
                    page.click('text="Serial"')
                except Exception:
                    print("[Scraper] Warning: Could not find 'Serial' on the page. Trying to find dashboard anyway...")
                
                print("[Scraper] Waiting for dashboard to load...")
                page.wait_for_selector('.tile-container', timeout=15000)
                print("[Scraper] Dashboard loaded! Waiting 10s for telemetry data to populate...")
                time.sleep(10) # Wait for all historical chart APIs to load
                
            except Exception as e:
                print(f"[Scraper] Warning: Navigation timed out or interrupted. Processing whatever data was collected.")
                try:
                    page.screenshot(path="scraper_debug.png")
                except:
                    pass
            finally:
                browser.close()
                
        # After browser is closed (even if errored!), process the data!
        if not tlog_data and not ilog_data:
            print("[Scraper] No datalogs found to process for this run.")
            return

        print("[Scraper] Processing datalogs into Supabase...")
        
        # Get latest timestamp from DB to prevent duplicates
        res = supabase.table("metrics_log").select("timestamp").eq("user_id", user_id).order("timestamp", desc=True).limit(1).execute()
        latest_ts = None
        if res.data and len(res.data) > 0:
            latest_ts = isoparse(res.data[0]["timestamp"])
        
        new_metrics = []
        
        # Process tlog
        for entry in tlog_data:
            dt = isoparse(entry.get("date"))
            if latest_ts and dt <= latest_ts:
                continue
                
            did = entry.get("did", "")
            val = entry.get("value")
            
            param_name = None
            if did.endswith("_0") and 5 < val < 15:
                param_name = "Alkalinity"
            elif did.endswith("_1") and 300 < val < 600:
                param_name = "Calcium"
            elif did.endswith("_2") and 1000 < val < 1600:
                param_name = "Magnesium"
                
            if param_name:
                new_metrics.append({
                    "user_id": user_id,
                    "parameter": param_name,
                    "value": float(val),
                    "timestamp": dt.isoformat()
                })
                
        # Process ilog
        for item in ilog_data:
            dt = isoparse(item.get("date"))
            if latest_ts and dt <= latest_ts:
                continue
                
            inputs = item.get("inputs", [])
            for inp in inputs:
                did = inp.get("did", "")
                val = inp.get("value")
                
                param_name = None
                if did.endswith("Temp"):
                    param_name = "Temperature"
                elif did.endswith("pH"):
                    param_name = "pH"
                elif did.endswith("Cond"):
                    param_name = "Salinity"
                elif did.endswith("ORP"):
                    param_name = "ORP"
                    
                if param_name:
                    new_metrics.append({
                        "user_id": user_id,
                        "parameter": param_name,
                        "value": float(val),
                        "timestamp": dt.isoformat()
                    })
                    
        if len(new_metrics) > 0:
            # Insert in chunks of 500 to avoid request size limits
            chunk_size = 500
            for i in range(0, len(new_metrics), chunk_size):
                chunk = new_metrics[i:i + chunk_size]
                try:
                    supabase.table("metrics_log").insert(chunk).execute()
                except Exception as e:
                    pass
            print(f"[Scraper] Inserted {len(new_metrics)} new records.")
        else:
            print("[Scraper] No new records to insert.")

    except Exception as e:
        import traceback
        with open("scraper_error.txt", "w") as f:
            f.write(traceback.format_exc())
        print(f"[Scraper] FATAL ERROR: {e}")


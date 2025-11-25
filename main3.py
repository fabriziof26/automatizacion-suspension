import asyncio
from playwright.async_api import async_playwright
from utils.ots import lista_ots, lista_ots_no_activas, observacion, ot_anulada, suspension_admin, excepcion_observa, subir_estado
from datetime import datetime
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

load_dotenv()
URL = os.getenv("URL")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
CONCURRENCY = 4

async def run_playwright_for_nrolote(nrolote):
    ots = lista_ots(nrolote)  # tu función que devuelve lista de OTs
    #lista_ots_no_activas(nrolote) # PREGUNTAR POR ESTA FUNCIONA YA QUE PARECE QUE ESTA MAL LA LOGICA
    hoy = datetime.today().strftime("%Y-%m-%d")
    results = []

    async def process_ot(ot, sem, pw):
        async with sem:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await page.goto(URL)
                await page.fill("#v_username", USER)
                await page.fill("#v_password", PASSWORD)
                await page.get_by_role("button", name="Ingresar").click()
                await asyncio.sleep(5)

                page1 = await context.new_page()
                await page1.goto(f"https://intranettraining.winempresas.pe/noc/ot_alta.php?v_codigo={ot}&v_area=operator")
                await page1.wait_for_load_state()
                html = await page1.content()
                soup = BeautifulSoup(html, 'html.parser')
                td_estado = soup.find("td", string=lambda t: t and t.strip() == "Estado")
                td_valor = td_estado.find_next("td")
                estado = td_valor.get_text(strip=True)
                subir_estado(nrolote, estado, ot)
                estado_minus = estado.lower()
                if estado_minus == "anulado":
                    ot_anulada(nrolote, ot)
                    suspension_admin(0, nrolote, ot)
                    print(f"ot: {ot} mensaje: Estado de OT Anulado, no se hizo la documentacion.")
                    return {"ot":ot, "mensaje":"Estado de OT Anulado, no se hizo la documentacion."}
                    
                await asyncio.sleep(2)
                print(f"INICIANDO SELECCION PARA LA OT {ot}...")
                # DESCOMENTAR ESTO EN PRODUCCIONNNNNNNNNNNNNNNNNNNNNNNNN
                #await page1.locator("#cboSubEstado").select_option("001")
                #print("sub estado")
                await page1.locator("#cboCategoria").select_option("032")
                print("categoria")
                await page1.locator("#cboGrupo").select_option("20")
                print("grupo")
        
                await page1.wait_for_function(
                    "document.querySelectorAll('#cboResponsable option').length > 1",
                    timeout=10000
                )
                
                await page1.evaluate(
                    """(fecha) => {
                        const input = document.querySelector("#alta_trabajo");
                        input.value = fecha;
                        input.dispatchEvent(new Event("change", { bubbles: true }));
                    }""",
                    hoy
                )
                await page1.locator("#btn_confirmar").click() # para guardar la fecha

                print("fecha ingresada: ", hoy)
                
                # Esperar un poco más para asegurar que todo esté listo
                await asyncio.sleep(1)
                
                await page1.locator("#cboResponsable").select_option("asegovia")
                print("responsable")
                
                await page1.get_by_role("button", name="Guardar").click()
                page1.once("dialog", lambda dialog: dialog.accept()) # esto es para grabar
                
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.get_by_role("link", name="Agregar Observacion").click()
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.locator("#v_new_observacion").click()
                obs = observacion(nrolote, ot)
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.locator("#v_new_observacion").fill(obs)

                # ESTO LO GUARDA
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.get_by_role("button", name="[+] Agregar Observacion").click()
                suspension_admin(1, nrolote, ot)
                print("TERMINO LA SELECCION...")
                await asyncio.sleep(900)

            except Exception as e:
                excepcion_observa(str(e), nrolote, ot)
                print("Error en OT", ot, e)
                
                return {"ot": ot, "status": "error", "error": str(e)}
            finally:
                await context.close()
                await browser.close()


    sem = asyncio.Semaphore(CONCURRENCY)
    async with async_playwright() as pw:
        tasks = [process_ot(ot, sem, pw) for ot in ots]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    return {"nrolote": nrolote, "hoy": hoy, "results": results}

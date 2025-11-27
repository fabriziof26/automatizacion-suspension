import asyncio
from playwright.async_api import async_playwright
from utils.ots import lista_ots, lista_ots_no_activas, observacion, ot_anulada, suspension_admin, excepcion_observa, subir_estado, lista_ots_no_suspendidas, grabar_logs
from datetime import datetime
from bs4 import BeautifulSoup


#### YA PARA SUBIR A PRODUCCION #####
import PT_Config
#####################################


URL = PT_Config.URL
SALTO_URL = PT_Config.SALTO_URL
CONCURRENCY = 4

# npx playwright codegen https://intranettraining.winempresas.pe/noc/ --target python

async def run_playwright_for_nrolote(nrolote, user, password):
    ots = lista_ots(nrolote)  # tu función que devuelve lista de OTs
    #lista_ots_no_activas(nrolote) # PREGUNTAR POR ESTA FUNCIONA YA QUE PARECE QUE ESTA MAL LA LOGICA
    lista_ots_no_suspendidas(nrolote)
    hoy = datetime.today().strftime("%Y-%m-%d")

    results = []

    async def process_ot(ot, sem, pw):
        async with sem:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                loop = asyncio.get_running_loop()
                
                ### INICIO DE SESION
                await loop.run_in_executor(None, grabar_logs, 'Ingresando a la Intranet', nrolote, ot)
                
                await page.goto(URL)
                await page.fill("#v_username", user)
                await page.fill("#v_password", password)
                await page.get_by_role("button", name="Ingresar").click()
                await asyncio.sleep(5)

                page1 = await context.new_page()
                
                await loop.run_in_executor(None, grabar_logs, 'Inicio de sesión exitosa', nrolote, ot)
                
                #### DOCUMENTACION DE LA OT
                url_documentacion = SALTO_URL+str(ot)
                #await page1.goto(f"https://intranettraining.winempresas.pe/noc/ot_alta.php?v_codigo={ot}&v_area=operator")
                await page1.goto(url_documentacion)
                await page1.wait_for_load_state()
                
                html = await page1.content()
                soup = BeautifulSoup(html, 'html.parser')
                td_estado = soup.find("td", string=lambda t: t and t.strip() == "Estado")
                td_valor = td_estado.find_next("td")
                estado = td_valor.get_text(strip=True)
                
                await loop.run_in_executor(None, grabar_logs, f'Obteniendo estado de la OT {ot}', nrolote, ot)
                
                
                estado_minus = estado.lower()
                if estado_minus == "anulado":
                    ot_anulada(nrolote, ot)
                    suspension_admin(0, nrolote, ot)
                    await loop.run_in_executor(None, grabar_logs, f'Estado de OT {ot} Anulado, no se hizo la documentacion."', nrolote, ot)
                    print(f"ot: {ot} mensaje: Estado de OT Anulado, no se hizo la documentacion.")
                    return {"ot":ot, "mensaje":"Estado de OT Anulado, no se hizo la documentacion."}
                    
                await asyncio.sleep(2)
                
                #### CATEGORIZACION DE LA OT
                
                print(f"INICIANDO SELECCION PARA LA OT {ot}...")
                # DESCOMENTAR ESTO EN PRODUCCIONNNNNNNNNNNNNNNNNNNNNNNNN
                #await page1.locator("#cboSubEstado").select_option("001")
                #await loop.run_in_executor(None, grabar_logs, f'Cambiando subestado de la OT {ot}', nrolote, ot)
                #print("sub estado")
                await page1.locator("#cboCategoria").select_option("032")
                await loop.run_in_executor(None, grabar_logs, f'Cambiando la categoria de la OT {ot}', nrolote, ot)
                print("categoria")
                await page1.locator("#cboGrupo").select_option("20")
                await loop.run_in_executor(None, grabar_logs, f'Cambiando el grupo de la OT {ot}', nrolote, ot)
                print("grupo")
                
                # Esperar un poco más para asegurar que todo esté listo
                await asyncio.sleep(1)
                
                await page1.wait_for_function(
                    "document.querySelectorAll('#cboResponsable option').length > 1",
                    timeout=10000
                )
                
                await page1.locator("#cboResponsable").select_option("asegovia")
                await loop.run_in_executor(None, grabar_logs, f'Cambiando el responsable de la OT {ot}', nrolote, ot)
                print("responsable")
                
                
                #page1.once("dialog", lambda dialog: dialog.dismiss()) # esto es para grabar
                #await page1.get_by_role("button", name="Guardar").click()
                guardar = page1.locator("//input[@type='button' and @value='Guardar' and @onclick='categorizarOt();']")
                page1.once("dialog", lambda dialog: dialog.accept())
                await guardar.click()
                print("Boton guardar")
                
                await loop.run_in_executor(None, grabar_logs, f'Guardando los cambios de la OT {ot}', nrolote, ot)

                await asyncio.sleep(3)
                
                ### COLOCANDO LA FECHA INICIAL
                
                await page1.evaluate(
                    """(fecha) => {
                        const input = document.querySelector("#alta_trabajo");
                        input.value = fecha;
                        input.dispatchEvent(new Event("change", { bubbles: true }));
                    }""",
                    hoy
                )
                
                await loop.run_in_executor(None, grabar_logs, f'Cambiando la fecha de ejecucion de la OT {ot}', nrolote, ot)
                guardar_fecha = page1.locator("//input[@type='button' and @id='btn_confirmar' and @value='Ejecutar']")
                page1.once("dialog", lambda dialog: dialog.accept()) # esto es para grabar, DESCOMENTAR CUANDO SE VAYA USAR
                #await page1.locator("#btn_confirmar").click() # para guardar la fecha
                await guardar_fecha.click()
                print("fecha ingresada: ", hoy)       
                
                await asyncio.sleep(3)
                
                #await page1.wait_for_load_state('networkidle')
                html_nuevo = await page1.content()
                soup_nuevo = BeautifulSoup(html_nuevo, 'html.parser')
                td_estado_nuevo = soup_nuevo.find("td", string=lambda t: t and t.strip() == "Estado")
                td_valor_nuevo = td_estado_nuevo.find_next("td")
                estado_nuevo = td_valor_nuevo.get_text(strip=True)
                
                
                subir_estado(nrolote, estado_nuevo, ot)

                await loop.run_in_executor(None, grabar_logs, f'Guardando el nuevo estado de la OT {ot}', nrolote, ot)
                
                ### GRABAR OBSERVACION
                
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.get_by_role("link", name="Agregar Observacion").click()
                await loop.run_in_executor(None, grabar_logs, f'Agregando observacion de la OT {ot}', nrolote, ot)
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.locator("#v_new_observacion").click()
                obs = observacion(nrolote, ot)
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.locator("#v_new_observacion").fill(obs)

                
                await page1.locator("iframe[name=\"iframeObservaciones\"]").content_frame.get_by_role("button", name="[+] Agregar Observacion").click() # ESTO LO GUARDA
                await loop.run_in_executor(None, grabar_logs, f'Guardando la observacion de la OT {ot}', nrolote, ot)
                suspension_admin(1, nrolote, ot)
                await loop.run_in_executor(None, grabar_logs, f'Documentación terminada de la OT {ot}', nrolote, ot)
                print("TERMINO LA SELECCION...")
                
                #await asyncio.sleep(900)

            except Exception as e:
                excepcion_observa('Ocurrió un error al intentar hacer la documentación', nrolote, ot)
                grabar_logs(str(e), nrolote, ot)
                print("Error en OT", ot, e)
                await loop.run_in_executor(None, grabar_logs, f'Ocurrió un error en la documentación de la OT {ot}', nrolote, ot)
                return {"ot": ot, "status": "error", "error": str(e)}
            finally:
                await context.close()
                await browser.close()


    sem = asyncio.Semaphore(CONCURRENCY)
    async with async_playwright() as pw:
        tasks = [process_ot(ot, sem, pw) for ot in ots]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    return {"nrolote": nrolote, "hoy": hoy, "results": results}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Error: falta nrolote")
        sys.exit(1)

    nrolote = sys.argv[1]
    user = sys.argv[2]
    password = sys.argv[3]
    print(f"Ejecutando con nrolote: {nrolote}")

    # correr la función principal
    asyncio.run(run_playwright_for_nrolote(nrolote, user, password))

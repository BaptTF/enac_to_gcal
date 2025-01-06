from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from time import sleep
from pathlib import Path
from datetime import datetime
import requests
import shutil
import os

def get_enac_ics(downloadPath, icsPath, url, user, password, nombre_de_mois):

    #nous devrions vérifier si le fichier existe ou non avant de le supprimer.
    print("processing", nombre_de_mois, "month" if nombre_de_mois > 1 else "months")
    if os.path.exists(icsPath + "/planning.ics"):
        print("Suppression du fichier: ", icsPath + "/planning.ics")
        os.remove(icsPath + "/planning.ics")
    else:
        print("Impossible de supprimer le fichier planning.ics car il n'existe pas")
    for i in range(1,nombre_de_mois):
        if os.path.exists(icsPath + f"/planning ({i}).ics"):
            os.remove(icsPath + f"/planning ({i}).ics")
        else:
            print(f"Impossible de supprimer le fichier planning ({i}).ics car il n'existe pas")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Run browser in headless mode
    #browser_locale = 'fr'
    #chrome_options.add_argument("--lang={}".format(browser_locale))
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    if driver.find_element(By.ID, "j_idt30:j_idt40_label").text != "Français":
        driver.find_element(By.XPATH, "//div[@class='ui-selectonemenu-trigger ui-state-default ui-corner-right']").click()
        sleep(2)
        driver.find_element(By.ID, "j_idt30:j_idt40_1").click()
        sleep(2)
        alert = Alert(driver)
        alert.accept()
        sleep(2)
    driver.find_element(By.ID, "username").send_keys(user)
    driver.find_element(By.ID, "password").send_keys(password)
    sleep(2)
    driver.find_element(By.ID, "j_idt28").click()
    driver.implicitly_wait(10)
    sleep(2)
    try:
        driver.find_element(By.LINK_TEXT, "Mon emploi du temps").click()
    except:
        driver.find_element(By.LINK_TEXT, "My schedule").click()
    driver.implicitly_wait(100)
    sleep(2)
    driver.find_element(By.XPATH, "//button[@class='fc-month-button ui-button ui-state-default ui-corner-left ui-corner-right']").click()
    sleep(5)
    print("Téléchargement du planning pour le mois: ", 1)
    driver.find_element(By.ID, "form:j_idt121").click()
    sleep(2)
    for _ in range(2,nombre_de_mois+1):
        try:
            print("Téléchargement du planning pour le mois: ", _)
            driver.find_element(By.XPATH, '//body').send_keys(Keys.CONTROL + Keys.HOME)
            sleep(5)
            driver.find_element(By.XPATH, "//button[@class='fc-next-button ui-button ui-state-default ui-corner-left ui-corner-right']").click()
            sleep(5)
            driver.find_element(By.ID, "form:j_idt121").click()
            sleep(5)
        except:
            print("Erreur lors du téléchargement du planning pour le mois: ", _)
    sleep(2)

    #cut paste the ics file
    if os.path.exists(downloadPath + "/planning.ics"):
        shutil.move(downloadPath + "/planning.ics", icsPath)
    else:
        print("Impossible de déplacer le fichier planning.ics car il n'existe pas")
    for i in range(1,nombre_de_mois):
        if os.path.exists(downloadPath + f"/planning ({i}).ics"):
            shutil.move(downloadPath + f"/planning ({i}).ics", icsPath)
        else:
            print(f"Impossible de déplacer le fichier planning ({i}).ics car il n'existe pas")

def get_enac_ics_request(user, password, nombre_de_mois):

    JSESSIONID = ""

    url = "https://aurion-prod.enac.fr/"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=0, i",
        "Connection": "close"
    }

    response = requests.get(url, headers=headers, allow_redirects=False)
    print("Status Code:", response.status_code)
    # print("Headers:", response.headers)
    JSESSIONID = response.headers.get("Set-Cookie").split(";")[0].split("=")[1]
    print("JESSIONID:", JSESSIONID)

    url = "https://aurion-prod.enac.fr/login"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Cookie": f"JSESSIONID={JSESSIONID};",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://aurion-prod.enac.fr",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://aurion-prod.enac.fr/faces/Login.xhtml",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=0, i",
        "Connection": "close"
    }
    data = {
        "username": user,
        "password": password,
        "j_idt28": ""
    }

    print("Headers:", headers)
    response = requests.post(url, headers=headers, data=data, allow_redirects=False)

    print("Status Code:", response.status_code)
    print("Response Text:", response.headers.get("Set-Cookie"))
    # print("Response Text:", response.text)
    if response.headers.get("Set-Cookie") is None:
        print("Mauvais mot de passe ou nom d'utilisateur")
        return
    JSESSIONID = response.headers.get("Set-Cookie").split(";")[0].split("=")[1]
    print("JESSIONID:", JSESSIONID)

    url = "https://aurion-prod.enac.fr/"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Cookie": f"JSESSIONID={JSESSIONID};",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Referer": "https://aurion-prod.enac.fr/faces/Login.xhtml",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=0, i",
        "Connection": "close"
    }

    response = requests.get(url, headers=headers)

    print("Status Code:", response.status_code)
    print("javax.faces.ViewState:", response.text[response.text.find("javax.faces.ViewState"):].split('value="')[1].split('"')[0])
    ViewState = response.text[response.text.find("javax.faces.ViewState"):].split('value="')[1].split('"')[0]

    url = "https://aurion-prod.enac.fr/faces/MainMenuPage.xhtml"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Cookie": f"JSESSIONID={JSESSIONID};",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://aurion-prod.enac.fr",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://aurion-prod.enac.fr/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=0, i",
        "Connection": "close"
    }
    data = {
        "form": "form",
        "form:largeurDivCenter": "1605",
        "form:idInit": "webscolaapp.MainMenuPage_5151765382358539267",
        "form:sauvegarde": "",
        "form:j_idt758:j_idt761_view": "basicDay",
        "form:j_idt884:j_idt886_dropdown": "1",
        "form:j_idt884:j_idt886_mobiledropdown": "1",
        "form:j_idt884:j_idt886_page": "0",
        "form:j_idt871_focus": "",
        "form:j_idt871_input": "44239",
        "javax.faces.ViewState": ViewState,
        "form:sidebar": "form:sidebar",
        "form:sidebar_menuid": "1"
    }

    response = requests.post(url, headers=headers, data=data)

    print("Status Code:", response.status_code)
    print("javax.faces.ViewState:", response.text[response.text.find("javax.faces.ViewState"):].split('value="')[1].split('"')[0])
    ViewState = response.text[response.text.find("javax.faces.ViewState"):].split('value="')[1].split('"')[0]

    url = "https://aurion-prod.enac.fr/faces/Planning.xhtml"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Cookie": f"JSESSIONID={JSESSIONID};",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Referer": "https://aurion-prod.enac.fr/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=0, i",
        "Connection": "close"
    }

    response = requests.get(url, headers=headers)

    print("Status Code:", response.status_code)
    print("javax.faces.ViewState:", response.text[response.text.find("javax.faces.ViewState"):].split('value="')[1].split('"')[0])
    ViewState = response.text[response.text.find("javax.faces.ViewState"):].split('value="')[1].split('"')[0]
    planningStr = response.text[response.text.find("webscolaapp.Planning_"):]
    # print("webscolaapp.Planning_:", planningStr)
    PlanningID = planningStr.split("_")[1].split('"')[0]
    print("PlanningID:", PlanningID)

    url = "https://aurion-prod.enac.fr/faces/Planning.xhtml"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Cookie": f"JSESSIONID={JSESSIONID};",
        "Sec-Ch-Ua": '"Chro ViewStmium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Faces-Request": "partial/ajax",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Origin": "https://aurion-prod.enac.fr",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://aurion-prod.enac.fr/faces/Planning.xhtml",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=1, i",
        "Connection": "close",
    }

    data = {
        "javax.faces.partial.ajax": "true",
        "javax.faces.source": "form:j_idt118",
        "javax.faces.partial.execute": "form:j_idt118",
        "javax.faces.partial.render": "form:j_idt118",
        "form:j_idt118": "form:j_idt118",
        "form:j_idt118_start": "1730070000000",
        "form:j_idt118_end": "1733526000000",
        "form": "form",
        "form:largeurDivCenter": "",
        "form:idInit": f"webscolaapp.Planning_{PlanningID}",
        "form:date_input": datetime.now().strftime("%d/%m/%Y"),
        "form:week": datetime.now().strftime("%W-%Y"),
        "form:j_idt118_view": "month",
        "form:offsetFuseauNavigateur": "-3600000",
        "form:onglets_activeIndex": "0",
        "form:onglets_scrollState": "0",
        "form:j_idt244_focus": "",
        "form:j_idt244_input": "44239",
        "javax.faces.ViewState": ViewState,
    }

    response = requests.post(url, headers=headers, data=data)

    print("Status Code:", response.status_code)
    # print("Response Text:", response.text)

    url = "https://aurion-prod.enac.fr/faces/Planning.xhtml"
    headers = {
        "Host": "aurion-prod.enac.fr",
        "Cookie": f"JSESSIONID={JSESSIONID};",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Upgrade-Insecure-Requests": "1",
        "Origin": "https://aurion-prod.enac.fr",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://aurion-prod.enac.fr/faces/Planning.xhtml",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Priority": "u=0, i",
        "Connection": "close"
    }

    data = {
        "form": "form",
        "form:largeurDivCenter": "1620",
        "form:idInit": f"webscolaapp.Planning_{PlanningID}",
        "form:date_input": datetime.now().strftime("%d/%m/%Y"),
        "form:week": datetime.now().strftime("%W-%Y"),
        "form:j_idt118_view": "month",
        "form:offsetFuseauNavigateur": "-3600000",
        "form:onglets_activeIndex": "0",
        "form:onglets_scrollState": "0",
        "form:j_idt244_focus": "",
        "form:j_idt244_input": "44239",
        "javax.faces.ViewState": ViewState,
        "form:j_idt121": "form:j_idt121",
    }

    response = requests.post(url, headers=headers, data=data)

    print("Status Code:", response.status_code)
    print("Response Text:", response.text)
    if response.status_code == 200:
        with open("ics/planning.ics", "w") as f:
            f.write(response.text)
    else:
        print("Erreur lors de la récupération du fichier ics")
        exit(1)


if __name__ == "__main__":
    config = {}
    config_path=os.environ.get('CONFIG_PATH', 'config.py')
    exec(Path(config_path).read_text(), config)
    feed = config.get('ICAL_FEEDS')[0]
    user = feed.get("ICAL_FEED_USER")
    pwd = feed.get("ICAL_FEED_PASS")
    month_to_sync = config.get('ICAL_DAYS_TO_SYNC') // 30
    print("month_to_sync: ", month_to_sync)
    # get_enac_ics(feed['download'],feed['source'],'https://aurion-prod.enac.fr/faces/Login.xhtml',user,pwd,month_to_sync)
    get_enac_ics_request(user,pwd,month_to_sync)

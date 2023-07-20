from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.common.by import By
import platform

app = Flask(__name__)


@app.route("/")
def hello_world():
    url = request.args.get('url')
    try:
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        print(platform.system())
        if platform.system() == "Windows":
            driver = webdriver.Chrome(r"C:\Users\asus\Downloads\chromedriver.exe", options=options)
        else:
            driver = webdriver.Chrome("/usr/bin/chromedriver", options=options)
        driver.implicitly_wait(100)

        driver.get(url)
        if driver.find_elements(By.CLASS_NAME, "sc-1bdyhrg-1")[0].text in ['Закрыто', 'Closed']:
            return 'closed'
        elem = driver.find_elements(By.CLASS_NAME, "hinTVF")[6]
        counter = 0
        result2 = elem.text.split()[-1]
        while result2 == '$-':
            result2 = elem.text.split()[-1]
            counter += 1
            if counter > 10000:
                break
        result = driver.find_elements(By.CLASS_NAME, "hinTVF")[0].text.split("\n")
        data = result.copy()
        result = f"{result[6]} {result[14]}, {result[9]}/{result[12]}"

        data = [data[1], data[8], data[11]]
        driver.close()
        return {
            'result': result,
            'data': data
        }
    except Exception as e:
        print(e)
        driver.close()
        return {
            'result': f'error {e}',
            'data': f'error'
        }


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)



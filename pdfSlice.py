# coding: utf-8
from requests import post
import json
import argparse
import base64
import re
import os

# Модуль по разделению PDF на страницы - ЧАСТЬ 1
from PyPDF2 import PdfFileReader, PdfFileWriter
pdf_document = r"C:\Users\gilr.SOFT-SERVIS.000\Desktop\SlicePDF\Scan1.pdf"
pdf = PdfFileReader(pdf_document)
for page in range(pdf.getNumPages()):
    pdf_writer = PdfFileWriter()
    current_page = pdf.getPage(page)
    pdf_writer.addPage(current_page)
    outputFilename = r"C:\Users\gilr.SOFT-SERVIS.000\Desktop\SlicePDF\Sliced\Slice-page-{}.pdf".format(page + 1)
    with open(outputFilename, "wb") as out:
        pdf_writer.write(out)
        print("created", outputFilename)

###############################################################
# Сканируем файлы в папке - ЧАСТЬ 2

directory = r'C:\Users\gilr.SOFT-SERVIS.000\Desktop\SlicePDF\Sliced'
file_list = os.listdir(directory)
full_list = [os.path.join(directory, i) for i in file_list]
time_sorted_list = sorted(full_list, key = os.path.getmtime)

print(time_sorted_list)
# Отправляем файл в Yandex OCR - ЧАСТЬ 3
check = []

for jpgFile in time_sorted_list:
    # Функция возвращает IAM-токен для аккаунта на Яндексе.
    def get_iam_token(iam_url, oauth_token):
        response = post(iam_url, json={"yandexPassportOauthToken": oauth_token})
        json_data = json.loads(response.text)
        if json_data is not None and 'iamToken' in json_data:
            return json_data['iamToken']
        return None


    # Функция отправляет на сервер запрос на распознавание изображения и возвращает ответ сервера.
    def request_analyze(vision_url, iam_token, folder_id, image_data):
        response = post(vision_url, headers={'Authorization': 'Bearer ' + iam_token}, json={
            'folderId': folder_id,
            'analyzeSpecs': [
                {
                    'content': image_data,
                    'mime_type': 'application/pdf', # Тип файла PDF
                    'features': [
                        {
                            'type': 'TEXT_DETECTION',
                            'textDetectionConfig': {'languageCodes': ['en', 'ru']}
                        }
                    ],
                }
            ]})
        return response.text


    def main():
        parser = argparse.ArgumentParser()
        # Если аргументы будем задавать через командную строку, то расскоментируем данный блок
        # parser.add_argument('--folder-id', required=True)
        # parser.add_argument('--oauth-token', required=True)
        # parser.add_argument('--image-path', required=True)
        args = parser.parse_args()

        folder_id = '' # Foled ID берем с Yandex Vision
        oauth_token = '' # OAuth токен берем с Yandex Vision
        image_path = jpgFile # Название файла для распознавания

        iam_url = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
        vision_url = 'https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze'

        iam_token = get_iam_token(iam_url, oauth_token)
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        response_text = request_analyze(vision_url, iam_token, folder_id, image_data)

        match = re.findall('\"text\":\s\".*\"', response_text)
        textStr = "".join(match)
        textStr = textStr.replace('"text":', '')
        textStr = textStr.replace('"', '')

        if textStr.find('ТОВАРНАЯ НАКЛАДНАЯ') or textStr.find('ТОРГ-12') or textStr.find('Универсальный передаточный документ') or (textStr.find('Счет-фактура') and textStr.find('Исправление')) != -1:
            indexStr = time_sorted_list.index(jpgFile)
            print("Да, есть ключевое слово. На странице номер: ", indexStr)
            check.append(indexStr)
        else:
            indexStr = time_sorted_list.index(jpgFile)
            print("НЕТ", indexStr)

        print('Сам текст: ' + textStr)

        # Сохранение распознанного текста в файл
        with open('text.txt', 'w') as txt_file:
            txt_file.write(textStr)


    if __name__ == '__main__':
        main()

# Временные данные, они есть наверху
# directory = r'C:\Users\Ринат\PycharmProjects\pdfSlice\Slice'
# file_list = os.listdir(directory)
# full_list = [os.path.join(directory, i) for i in file_list]
# time_sorted_list = sorted(full_list, key = os.path.getmtime)

# Собираем отдельные страницы в документы - ЧАСТЬ 4

pdfs = []
from PyPDF2 import PdfFileMerger
check = [0, 3]
print(len(time_sorted_list))
for k in check:
    try:
        check[k+1]
    except LookupError:
        stop = len(time_sorted_list)
    else:
        stop = check[k+1]
    for i in range(k, stop):
        print('Hello')
        pdfs.append(time_sorted_list[i])

    print(pdfs)
    merger = PdfFileMerger()

    for pdf in pdfs:
        merger.append(pdf)

    merger.write('C:/Users/gilr.SOFT-SERVIS.000/Desktop/SlicePDF/result{}.pdf'.format(k))
    merger.close()
    pdfs = []
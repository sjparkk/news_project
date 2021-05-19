from flask import Flask, render_template, jsonify, request, send_file
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup

client_id = "iT40oCtuzAgvWY4Zl1p8"
client_secret = "hblvKZHGQF"

news = Flask(__name__)

client = MongoClient('mongodb://test:test@localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbsparta  # 'dbsparta'라는 이름의 db를 만들거나 사용합니다.

## HTML을 주는 부분
@news.route('/')
def home():
    return render_template('index.html')

@news.route('/memo', methods=['POST'])
def post_article():
    header = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    #meta tag 스크래핑 - 네이버 api 에서 이미지를 제공하지 않아 meta tag 안에 있는 image 스크래핑
    headers_meta = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    #네이버 뉴스 api news
    keyword_receive = request.form.get('keyword_give')
    max_display = request.form.get('max_display_give')
    url = "https://openapi.naver.com/v1/search/news.json"
    query_url = f"{url}?query={keyword_receive}&display={str(int(max_display))}"

    response = requests.get(query_url, headers=header)
    responses = response.json()
    items = responses['items']
    articles = []

    for item in items:
        url_receive = item['originallink']
        data = requests.get(url_receive, headers=headers_meta)
        soup = BeautifulSoup(data.text, 'html.parser')
        meta_tag = soup.select_one('meta[property="og:image"]')
        if meta_tag['content']:
            og_image = meta_tag['content']
        elif 'sized' in meta_tag['content']:
            og_image = ''
        else :  # 이미지 없을 시 대체 이미지
            og_image = ''

        article = {'originallink': item['originallink'], 'image': og_image, 'title': item['title'], 'description': item['description'], 'isScraped': False}
        articles.append(article)

    return jsonify({'result': 'success', 'articles': articles})

@news.route('/scraped', methods = ['POST'])
def post_scraped_articles():
    originallink = request.form.get('scraped_originallink')

    # meta tag 스크래핑 - 데이터 자체에 "" 값이 있으면 충돌 발생하여 정확한 값을 가져오기 위한 스크래핑
    headers_originallink = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(originallink, headers=headers_originallink)
    soup = BeautifulSoup(data.text, 'html.parser')

    og_originallink = soup.select_one('meta[property="og:url"]')
    og_image = soup.select_one('meta[property="og:image"]')
    og_title = soup.select_one('meta[property="og:title"]')
    og_description = soup.select_one('meta[property="og:description"]')

    news_originallink = og_originallink['content']
    news_image = og_image['content']
    news_title = og_title['content']
    news_description = og_description['content']
    news_scraped = True

    news_article = {
        'description': news_description,
        'originallink': news_originallink,
        'title': news_title,
        'image': news_image,
        'isScraped': news_scraped
    }

    db.articles.insert_one(news_article)

    return jsonify({'result': 'success'})

# db 에 있는 정보 전달
@news.route('/memo', methods=['GET'])
def read_articles():
    # mongoDB에서 _id 값을 제외한 모든 데이터 조회해오기 (Read)
    result = list(db.articles.find({}, {'_id': 0}))
    # articles라는 키 값으로 article 정보 보내주기
    return jsonify({'result': 'success', 'articles': result})

# 대체 이미지
@news.route('/images', methods=['GET'])
def get_image():
    file_path = 'static/' + 'noImage.jpg'
    return send_file(file_path, mimetype='noImage/jpg')

# 전체 삭제
@news.route('/delete', methods=['POST'])
def delete_articles():
    db.articles.remove({})
    return jsonify({'result': 'success', 'msg': '삭제가 완료되었습니다!'})

if __name__ == '__main__':
    news.run('0.0.0.0', port=5000, debug=True)

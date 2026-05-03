import os
from flask import Flask, send_file, jsonify
import openpyxl
from collections import Counter

# Flask 앱 초기화
app = Flask(__name__, static_folder='static')

@app.route('/')
def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, 'index.html')
    
    return send_file(index_path)

# [추가됨] 인기 검색어 API 라우트
@app.route('/api/trending')
def get_trending():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # static 폴더 안의 searchlist.xlsx 경로 지정
    file_path = os.path.join(base_dir, 'static', 'searchlist.xlsx')
    
    try:
        # 엑셀 파일 로드 (수식 제외 데이터만 읽기)
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active
        
        search_terms = []
        # A열(첫 번째 열)의 모든 데이터를 순회하며 추출
        for row in sheet.iter_rows(min_col=1, max_col=1, values_only=True):
            term = row[0]
            # 빈 칸이 아니고 값이 존재하는 경우에만 리스트에 추가
            if term:
                search_terms.append(str(term).strip())
        
        # 빈도수 계산 (Counter 객체가 자동으로 개수를 세어줍니다)
        counter = Counter(search_terms)
        
        # 가장 많이 나온 상위 3개 추출 [(검색어, 횟수), (검색어, 횟수), ...]
        top_3 = counter.most_common(3)
        
        # 프론트엔드(index.html)가 요구하는 JSON 형태로 변환
        # 예: [{'id': 1, 'term': '검색어1'}, {'id': 2, 'term': '검색어2'}, ...]
        results = [{'id': idx + 1, 'term': item[0]} for idx, item in enumerate(top_3)]
        
        return jsonify(results)
        
    except FileNotFoundError:
        print("searchlist.xlsx 파일이 없습니다.")
        return jsonify([]) # 파일이 없으면 빈 배열 반환 (오류 방지)
    except Exception as e:
        print(f"엑셀 읽기 오류: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

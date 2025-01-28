from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from fuzzywuzzy import process

app = Flask(__name__)
CORS(app)  # 允许跨域请求

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')

    files=[f"jpg_{i+1:02}\\index.csv" for i in range(13)]
    df=pd.concat([pd.read_csv(file) for file in files],axis=0,ignore_index=True)
    choices=df['content']
    matches=process.extract(query,choices,limit=6)
    sentences=list(set([i[0] for i in matches]))
    df=pd.concat([df[df['content']==sentence] for sentence in sentences],axis=0,ignore_index=True)
    images=df['path'].to_list()
    images=images[:6]

    return jsonify({"images": images})

if __name__ == '__main__':
    app.run(debug=True)
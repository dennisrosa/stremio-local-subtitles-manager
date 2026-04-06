import os
import json
import uuid
import time
import argparse
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('stremio_addon')

# Memória de Staging em memória RAM do module level
staging_list = []

def create_app(storage_path):
    app = Flask(__name__)
    CORS(app)

    os.makedirs(storage_path, exist_ok=True)

    @app.before_request
    def log_request_info():
        logger.info(f"REQUEST RECEBIDO: {request.method} {request.url}")

    @app.route('/')
    def index():
        import socket
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
        except:
            lan_ip = "127.0.0.1"
        return render_template('index.html', lan_ip=lan_ip)

    @app.route('/manifest.json')
    def get_manifest():
        manifest = {
            "id": "com.local.subtitles.manager",
            "version": "1.0.0",
            "name": "SLSM - Stremio Local Subtitles Manager",
            "description": "Intercepta demandas do Stremio e providencia autorização para pastas de legendas locais.",
            "idPrefixes": ["tt"],
            "resources": ["subtitles"],
            "types": ["movie", "series"],
            "catalogs": [],
            "behaviorHints": {
                "configurable": True,
                "configurationRequired": True
            }
        }
        return jsonify(manifest)

    @app.route('/subtitles/<media_type>/<media_id>.json')
    @app.route('/subtitles/<media_type>/<media_id>/<extra>.json')
    def get_subtitles(media_type, media_id, extra=None):
        logger.info(f"Busca de Legenda (Stremio): type={media_type}, id={media_id}, extra={extra}")
        
        movie_id = media_id
        season = None
        episode = None
        
        if media_type == 'series' and ':' in media_id:
            parts = media_id.split(':')
            if len(parts) >= 3:
                movie_id = parts[0]
                season = int(parts[1])
                episode = int(parts[2])

        if media_type == 'movie':
            target_dir = os.path.join(storage_path, 'movies', movie_id)
        else:
            if season is not None and episode is not None:
                target_dir = os.path.join(storage_path, 'series', movie_id, f"season_{season:02d}", f"episode_{episode:02d}")
            else:
                target_dir = os.path.join(storage_path, 'series', movie_id)

        target_dir_abs = os.path.abspath(target_dir)

        # Verifica se os arquivos de fato existem localmente
        files_found = []
        if os.path.exists(target_dir_abs):
            for f in os.listdir(target_dir_abs):
                if f.endswith(('.srt', '.vtt', '.ass')):
                    files_found.append(f)
        
        if files_found:
            logger.info(f"-> SUCESSO: Foram encontradas {len(files_found)} legendas em {target_dir_abs}")
            subtitles_data = []
            for file in files_found:
                lower_f = file.lower()
                lang_code = "por"
                
                if "eng" in lower_f or "en." in lower_f or "_en" in lower_f.replace("-en", "_en"):
                    lang_code = "eng"
                elif "spa" in lower_f or "es." in lower_f or "_es" in lower_f.replace("-es", "_es"):
                    lang_code = "spa"
                elif "fre" in lower_f or "fr." in lower_f or "_fr" in lower_f.replace("-fr", "_fr"):
                    lang_code = "fre"
                    
                subtitles_data.append({
                    "id": file,
                    "url": f"{request.host_url}direct_subtitle/{media_type}/{media_id.replace(':', '_')}/{file}",
                    "lang": lang_code
                })
            return jsonify({"subtitles": subtitles_data})
        
        global staging_list
        already_staged = any(s.get('media_id') == movie_id and s.get('season') == season and s.get('episode') == episode for s in staging_list)
        if not already_staged:
            extra_info = {}
            if extra:
                for pair in extra.split('&'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        extra_info[k] = v
                        
            new_staging = {
                "id": str(uuid.uuid4()),
                "type": media_type,
                "media_id": movie_id,
                "season": season,
                "episode": episode,
                "language": "por",
                "target_dir": target_dir_abs,
                "detected_at": int(time.time()),
                "extra_info": extra_info
            }
            staging_list.append(new_staging)
            logger.warning(f"-> NÃO ENCONTRADO localmente. Requisição para a criação da base de {movie_id} adicionada ao Staging.")
        else:
            logger.info(f"-> NÃO ENCONTRADO localmente (Mas a pendência estrutural do ID {movie_id} já consta no Staging).")

        return jsonify({"subtitles": []})

    @app.route('/staged', methods=['GET'])
    def get_staged():
        return jsonify({"pending": staging_list})

    @app.route('/staged/all', methods=['DELETE'])
    def clear_staged():
        global staging_list
        staging_list.clear()
        logger.info("-> TODAS as pendencias do Staging foram esvaziadas globalmente via UI.")
        return jsonify({"status": "ok", "message": "Queue cleared"}), 200

    @app.route('/authorize/<req_id>', methods=['POST'])
    def authorize_staged(req_id):
        global staging_list
        item = next((s for s in staging_list if s['id'] == req_id), None)
        if not item:
            return jsonify({"error": "Not found in staging"}), 404
            
        os.makedirs(item['target_dir'], exist_ok=True)
        staging_list = [s for s in staging_list if s['id'] != req_id]
        logger.info(f"-> AUTORIZADO: Pasta {item['target_dir']} física foi criada.")
        return jsonify({"status": "ok"})

    @app.route('/authorize/all', methods=['POST'])
    def authorize_all():
        global staging_list
        for item in staging_list:
            os.makedirs(item['target_dir'], exist_ok=True)
        count = len(staging_list)
        staging_list.clear()
        logger.info(f"-> TODAS PASTAS AUTORIZADAS: {count} diretórios construídos fisicamente no disco.")
        return jsonify({"status": "ok", "created": count})

    @app.route('/directories', methods=['GET'])
    def list_created_directories():
        valid_dirs = []
        for base in ['movies', 'series']:
            base_path = os.path.join(storage_path, base)
            if os.path.exists(base_path):
                for root, d_names, f_names in os.walk(base_path):
                    rel_path = os.path.relpath(root, storage_path).replace('\\', '/')
                    if rel_path == base: continue
                    
                    parts = rel_path.split('/')
                    if base == 'series' and len(parts) < 4: continue
                    
                    metadata = {
                        "path": rel_path,
                        "type": base[:-1],
                        "media_id": parts[1]
                    }
                    
                    if base == 'series' and len(parts) >= 4:
                        metadata["season"] = parts[2].split('_')[1]
                        metadata["episode"] = parts[3].split('_')[1]
                        
                    subs = []
                    for f in f_names:
                        if f.lower().endswith(('.srt', '.vtt', '.ass')):
                            lang_code = "por"
                            lower_f = f.lower()
                            if "eng" in lower_f or "en." in lower_f or "_en" in lower_f.replace("-en", "_en"): lang_code = "eng"
                            elif "spa" in lower_f or "es." in lower_f or "_es" in lower_f.replace("-es", "_es"): lang_code = "spa"
                            elif "fre" in lower_f or "fr." in lower_f or "_fr" in lower_f.replace("-fr", "_fr"): lang_code = "fre"
                            subs.append({"filename": f, "lang": lang_code})
                            
                    metadata["subtitles"] = subs
                    valid_dirs.append(metadata)
                    
        valid_dirs.sort(key=lambda x: x["path"], reverse=True)
        return jsonify({"directories": valid_dirs})

    @app.route('/directory/<path:dir_path>', methods=['DELETE'])
    def delete_directory(dir_path):
        target_abs = os.path.abspath(os.path.join(storage_path, dir_path))
        if not target_abs.startswith(os.path.abspath(storage_path)):
            return jsonify({"error": "Caminho inválido"}), 400
            
        if os.path.exists(target_abs) and os.path.isdir(target_abs):
            try:
                shutil.rmtree(target_abs)
                logger.info(f"-> DELETE DE SUCESSO: O diretório em folha {target_abs} foi explodido junto à todas suas legendas associadas.")
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        return jsonify({"error": "Diretório não encontrado ou inexistente"}), 404

    @app.route('/upload', methods=['POST'])
    def perform_upload():
        if 'file' not in request.files:
            return jsonify({"error": "Arquivo não providenciado"}), 400
            
        file = request.files['file']
        target_rel = request.form.get('target_dir')
        if not file or file.filename == '':
            return jsonify({"error": "Nome de arquivo vazio"}), 400
        if not target_rel:
            return jsonify({"error": "Destino não informado"}), 400
            
        if not file.filename.lower().endswith(('.srt', '.vtt', '.ass')):
            return jsonify({"error": "Restrito a arquivos de legenda (.srt, .vtt, .ass)"}), 400
            
        target_abs = os.path.abspath(os.path.join(storage_path, target_rel))
        if not target_abs.startswith(os.path.abspath(storage_path)):
            return jsonify({"error": "Caminho inválido"}), 400
            
        if not os.path.exists(target_abs):
            return jsonify({"error": "Caminho root estipulado não se encontra criado fisicamente (400 Bad Request)"}), 400
            
        filename = secure_filename(file.filename)
        dest = os.path.join(target_abs, filename)
        file.save(dest)
        logger.info(f"-> UPLOAD DE SUCESSO: Arquivo {filename} populou a pasta local -> {dest}")
        
        return jsonify({"status": "ok", "message": "Uploaded successfully to " + filename})

    @app.route('/direct_subtitle/<media_type>/<media_id>/<filename>')
    def serve_direct_subtitle(media_type, media_id, filename):
        movie_id = media_id
        season = None
        episode = None
        
        if media_type == 'series' and '_' in media_id:
            parts = media_id.split('_')
            if len(parts) >= 3:
                movie_id = parts[0]
                season = int(parts[1])
                episode = int(parts[2])

        if media_type == 'movie':
            target_dir = os.path.join(storage_path, 'movies', movie_id)
        else:
            target_dir = os.path.join(storage_path, 'series', movie_id, f"season_{season:02d}", f"episode_{episode:02d}")

        return send_from_directory(os.path.abspath(target_dir), filename)

    return app

def main():
    parser = argparse.ArgumentParser(description="SLSM - Stremio Local Subtitles Manager")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host/IP local ou externo para parear o servidor")
    parser.add_argument("--port", type=int, default=3001, help="Porta para rodar o servidor web")
    parser.add_argument("--storage-path", type=str, default="./subtitles_data", help="Caminho recursivo raiz para gerenciar e armazenar the legendas")
    
    args = parser.parse_args()
    
    logger.info(f"Iniciando SLSM Server no Host {args.host}:{args.port} | Pasta local storage principal fixada em: {os.path.abspath(args.storage_path)}")
    
    # Debug False for running as package daemon safely
    app = create_app(args.storage_path)
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()

from inspect import ArgSpec
from flask import Blueprint, request, jsonify
import validators

from src.constants.http_status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from src.database import Bookmark, db
from flasgger import Swagger, swag_from
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended.view_decorators import jwt_required
bookmarks = Blueprint("bookmarks", __name__, url_prefix="/api/v1/bookmarks")

@bookmarks.route('/', methods=['POST','GET'])  # type: ignore
@jwt_required()
def bookmarks_handler():
    current_user = get_jwt_identity()

    if request.method == 'POST':

        body = request.json.get('body','') #type: ignore
        url = request.json.get('url','')#type: ignore

        if not validators.url(url):
            return jsonify({
                'error':'Enter a valid url'
            }), HTTP_400_BAD_REQUEST

        bookmark = Bookmark.query.filter_by(url=url).first()

        if bookmark:
            return jsonify({
                'error':'URL already exists'
            }), HTTP_409_CONFLICT

        bookmark = Bookmark(body = body, url = url, user_id = current_user)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            "message":"Bookmark created successfully",
            "bookmark": {
                "bookmark_id": bookmark.id,
                "body": bookmark.body,
                "url": bookmark.url,
                "user_id": bookmark.user_id,
                "visits": bookmark.vists,
                "created_at": bookmark.created_at,
                "updated_at": bookmark.updated_at,
                "short_url": bookmark.short_url
            }
        }), HTTP_200_OK

    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type = int)
        bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

        data = []

        for item in bookmarks.items:
            data.append({
                'id': item.id,
                'body': item.body,
                'url': item.url,
                'short_url': item.short_url,
                'visits' : item.vists,
                'user_id': item.user_id,
                'created_at': item.created_at, 
                'updated_at': item.updated_at
            })
        
        meta={
            "page": bookmarks.page,
            "pages": bookmarks.pages,
            "total_count": bookmarks.total,
            "prev_page": bookmarks.prev_num,
            "next_page": bookmarks.next_num,
            "has_next": bookmarks.has_next,
            "has_prev": bookmarks.has_prev
        }

        return jsonify({"data":data, "meta": meta}), HTTP_200_OK

@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    current_user=get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id = id).first()

    if not bookmark:
        return jsonify({
            'message':'Item not found'
        }), HTTP_404_NOT_FOUND

    return jsonify({ 
            "bookmark_id": bookmark.id,
            "body": bookmark.body,
            "url": bookmark.url,
            "user_id": bookmark.user_id,
            "visits": bookmark.vists,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at,
            "short_url": bookmark.short_url
        }), HTTP_200_OK

@bookmarks.put('/<int:id>')
@bookmarks.patch('/<int:id>')
@jwt_required()
def editbookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id = current_user, id = id).first()


    if not bookmark:
        return jsonify({
            "message": "Item not found"
        }), HTTP_404_NOT_FOUND

    body = request.json.get('body', '') #type: ignore
    url = request.json.get('url', '') #type: ignore

    if not validators.url(url):
        return jsonify({
            'error':'Enter a valid url'
        }), HTTP_400_BAD_REQUEST

    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return jsonify({
            "bookmark_id": bookmark.id,
            "body": bookmark.body,
            "url": bookmark.url,
            "user_id": bookmark.user_id,
            "visits": bookmark.vists,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at,
            "short_url": bookmark.short_url
        }), HTTP_200_OK

@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id = current_user, id = id).first()

    if not bookmark:
        return jsonify({
            "message": "Item not found"
        }), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()
    
    return jsonify({}), HTTP_204_NO_CONTENT

@bookmarks.get("/stats")
@jwt_required()
@swag_from('../docs/bookmarks/stats.yaml')
def get_stat():
    current_uesr = get_jwt_identity()
    data = []

    items = Bookmark.query.filter_by(user_id = current_uesr).all()
    
    for item in items:
        data.append({
            'url': item.url,
            'vists': item.vists,
            'short_url': item.short_url,
            'id': item.id
        })

    return jsonify({'data': data}), HTTP_200_OK



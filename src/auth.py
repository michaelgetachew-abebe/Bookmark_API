import json
from flask import Blueprint, app, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flasgger import Swagger, swag_from
from src.database import User,db
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.post('/register')
@swag_from('../docs/auth/register.yaml')
def register():
    req = request.get_json()
    username = req['username']  # type: ignore
    email = req['email']  # type: ignore
    password = req['password']  # type: ignore

    if len(password) < 6:
        return jsonify({'error':'Password is too short'}), HTTP_400_BAD_REQUEST

    if len(username) < 3:
        return jsonify({'error':'Username is too short'}), HTTP_400_BAD_REQUEST

    if not username.isalnum() or " " in username:
        return jsonify({'error':'Username should be alphanumeric and no spaces'}), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({'error':'Invalid Email format'})

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error':'Email already exists'}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error':'Username is already taken'}), HTTP_409_CONFLICT
    
    hashed_pwd = generate_password_hash(password)

    user = User(username=username, password=hashed_pwd, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message':'User is successfully created',
        'user': {
            'username': username,
            'email': email
        }
    }), HTTP_201_CREATED

@auth.post('/login')  # type: ignore
@swag_from('../docs/auth/login.yaml')
def login():
    email = request.json.get('email', '') # type: ignore
    password = request.json.get('password', '') # type: ignore

    user = User.query.filter_by(email = email).first()

    if user:
        is_password_correct = check_password_hash(user.password, password)

        if is_password_correct:
            # Create access token and refresh token
            refresh = create_refresh_token(identity = user.id)
            access = create_access_token(identity = user.id)

            return jsonify({
                'message':'Login is successful',
                'user': {
                    'refersh': refresh,
                    'access': access,
                    'username': user.username,
                    'email': user.email
                }
            }), HTTP_202_ACCEPTED

    return jsonify({
            'message':'Wrong Credentials'
        }), HTTP_401_UNAUTHORIZED

@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    return jsonify({
        'username': user.username,
        'email': user.email
    }), HTTP_200_OK

@auth.post("/token/refresh")
@jwt_required(refresh = True)
def refresh_user_token():
    identity = get_jwt_identity()
    access = create_access_token(identity = identity)

    return jsonify({
        'access': access
    }), HTTP_200_OK

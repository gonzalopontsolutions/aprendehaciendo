# import logging
# from channels.middleware import BaseMiddleware
# from channels.db import database_sync_to_async
# from django.contrib.auth.models import AnonymousUser
# from urllib.parse import parse_qs
# from users.models import Token
# from rest_framework_simplejwt.tokens import AccessToken
# import jwt
# from django.conf import settings

# logger = logging.getLogger(__name__)

# @database_sync_to_async
# def get_user_from_token(token_key):
#     try:
#         # Intentar decodificar el token JWT primero
#         logger.info(f"Intentando decodificar token JWT: {token_key[:20]}...")
        
#         # Primero intentar con el token almacenado
#         token_obj = Token.objects.filter(access_token=token_key).first()
#         if token_obj:
#             logger.info(f"Token encontrado en BD para usuario: {token_obj.user.email}")
#             return token_obj.user

#         # Si no está en BD, intentar decodificar el JWT
#         try:
#             decoded_token = AccessToken(token_key)
#             user_id = decoded_token['user_id']
#             from users.models import User
#             user = User.objects.get(id=user_id)
#             logger.info(f"Usuario encontrado por JWT: {user.email}")
#             return user
#         except Exception as jwt_error:
#             logger.error(f"Error decodificando JWT: {str(jwt_error)}")
#             raise

#     except Exception as e:
#         logger.error(f"Error de autenticación: {str(e)}")
#         return AnonymousUser()

# class TokenAuthMiddleware(BaseMiddleware):
#     async def __call__(self, scope, receive, send):
#         try:
#             query_string = scope.get('query_string', b'').decode()
#             logger.info(f"Query string recibida: {query_string}")
            
#             query_params = parse_qs(query_string)
#             token = query_params.get('token', [None])[0]

#             if token:
#                 logger.info(f"Token recibido: {token[:20]}...")
#                 scope['user'] = await get_user_from_token(token)
                
#                 if isinstance(scope['user'], AnonymousUser):
#                     logger.warning("Usuario anónimo - token inválido o expirado")
#                 else:
#                     logger.info(f"Usuario autenticado correctamente: {scope['user'].email}")
#             else:
#                 logger.warning("No se recibió token")
#                 scope['user'] = AnonymousUser()

#         except Exception as e:
#             logger.error(f"Error en middleware: {str(e)}")
#             scope['user'] = AnonymousUser()

#         return await super().__call__(scope, receive, send)
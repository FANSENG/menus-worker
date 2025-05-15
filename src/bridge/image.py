import base64
import re
import time
import random
import json
import tos

# 从环境变量中获取配置
TOS_REGION = 'cn-beijing'
TOS_ENDPOINT = 'tos-cn-beijing.volces.com'
TOS_BUCKET_NAME = 'menus'

# 全局客户端变量
client = None

def initialize_tos_client(env):
    """
    初始化TOS客户端
    
    Args:
        env: 包含TOS访问密钥的环境变量
        
    Returns:
        TOS客户端实例
    """
    global client
    if not client:
        client = tos.TosClientV2(
            ak= env.TOS_ACCESS_KEY,
            sk= env.TOS_SECRET_KEY,
            endpoint=TOS_ENDPOINT,
            region=TOS_REGION
        )
    return client

def handle_error(error):
    """
    处理TOS SDK相关的错误
    
    Args:
        error: 错误对象
        
    Raises:
        Exception: 重新抛出格式化后的错误
    """
    # 获取错误类型
    error_type = str(type(error).__name__)
    
    if 'TosClientError' in error_type:
        print(f'TOS Client Error: {error}')
        raise Exception(f'TOS Client Error: {error}')
    elif 'TosServerError' in error_type:
        # 尝试从错误对象中提取信息
        try:
            request_id = getattr(error, 'requestId', 'Unknown')
            status_code = getattr(error, 'statusCode', 'Unknown')
            code = getattr(error, 'code', 'Unknown')
            message = str(error)
            
            print(f'TOS Server Error Request ID: {request_id}')
            print(f'TOS Server Error Status Code: {status_code}')
            print(f'TOS Server Error Code: {code}')
            print(f'TOS Server Error Message: {message}')
            
            raise Exception(f'TOS Server Error ({code}): {message}')
        except Exception as e:
            print(f'Error while processing TosServerError: {e}')
            raise Exception(f'TOS Server Error: {error}')
    else:
        print(f'Unexpected error: {error}')
        raise Exception('An unexpected error occurred while interacting with TOS.')

async def get_pre_signed_download_url(env, image_path):
    """
    获取图片的预签名下载链接
    
    Args:
        env: 包含TOS访问密钥的环境变量
        image_path: 图片在存储桶中的路径/名称 (key)
        
    Returns:
        预签名的下载URL字符串
        
    Raises:
        Exception: 如果配置缺失或生成URL失败
    """
    if not all([TOS_REGION, TOS_ENDPOINT, TOS_BUCKET_NAME]):
        print('Missing TOS configuration in environment variables.')
        raise Exception('TOS configuration is incomplete. Please check environment variables: TOS_ACCESS_KEY, TOS_SECRET_KEY, TOS_REGION, TOS_ENDPOINT, TOS_BUCKET_NAME.')
    
    try:
        tos_client = initialize_tos_client(env)
        # 通过FFI调用JavaScript方法
        url = tos_client.getPreSignedUrl({
            'method': 'GET',  # 指定操作为下载
            'bucket': TOS_BUCKET_NAME,
            'key': image_path,
            # 'expires': 3600,  # 链接有效期，单位秒，默认为3600秒 (1小时)，可以按需调整
        })
        return url
    except Exception as error:
        handle_error(error)  # 错误将在这里被捕获并重新抛出
        return ''  # 由于handle_error会抛出错误，这里的return实际上不会执行

def get_file_extension_from_base64(base64_data):
    """
    从Base64图片数据中获取文件扩展名
    
    Args:
        base64_data: Base64编码的图片数据
        
    Returns:
        文件扩展名（不包含点）
    """
    # 检查是否包含MIME类型前缀
    if base64_data.startswith('data:image/'):
        mime_type = base64_data.split(';')[0].split(':')[1]
        # 从MIME类型中提取扩展名
        extension = mime_type.split('/')[1]
        return 'jpg' if extension == 'jpeg' else extension
    
    # 如果没有MIME类型前缀，默认返回jpg
    return 'jpg'

async def upload_image_to_storage(env, image_data):
    """
    将Base64编码的图片数据上传到对象存储
    
    Args:
        env: 环境变量，包含TOS访问密钥
        image_data: 图片数据, Base64编码
        
    Returns:
        上传后的Key
        
    Raises:
        Exception: 如果配置缺失或上传失败
    """
    if not all([TOS_REGION, TOS_ENDPOINT, TOS_BUCKET_NAME]):
        print('Missing TOS configuration in environment variables.')
        raise Exception('TOS configuration is incomplete. Please check environment variables: TOS_ACCESS_KEY, TOS_SECRET_KEY, TOS_REGION, TOS_ENDPOINT, TOS_BUCKET_NAME.')
    
    # 检查image_data是否为Base64格式
    if not image_data or not isinstance(image_data, str):
        raise Exception('Invalid image data: Image data must be a non-empty string')
    
    # 如果Base64字符串包含前缀（如data:image/jpeg;base64,），则移除前缀
    base64_data = re.sub(r'^data:image/(png|jpeg|jpg|gif);base64,', '', image_data)
    
    # 在Cloudflare Workers环境中解码Base64
    # 使用Python的base64模块解码
    image_buffer = base64.b64decode(base64_data)
    
    # 生成唯一的文件名（使用时间戳和随机字符串）
    timestamp = int(time.time() * 1000)
    random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    file_extension = get_file_extension_from_base64(image_data)
    key = f'images/{timestamp}-{random_string}.{file_extension}'
    
    try:
        # 初始化TOS客户端并上传文件
        tos_client = initialize_tos_client(env)
        
        # 通过FFI调用JavaScript方法
        await tos_client.putObject({
            'bucket': TOS_BUCKET_NAME,
            'key': key,
            'body': image_buffer,
            'contentType': f'image/{file_extension}',
        })
        
        print(f'Successfully uploaded image to {key}')
        return key
    except Exception as error:
        handle_error(error)
        return ''  # 由于handle_error会抛出错误，这里的return实际上不会执行
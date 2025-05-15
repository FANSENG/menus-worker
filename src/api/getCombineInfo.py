from typing import TypedDict, List
from fastapi import Request

class Menu(TypedDict):
    id: int
    name: str
    image: str

class Category(TypedDict):
    name: str

class Dish(TypedDict):
    name: str
    image: str
    categoryName: str

class CombineInfoResponse(TypedDict):
    menu: Menu
    categories: List[Category]
    dishes: List[Dish]

async def get_combine_info_api(request: Request):
    id_string = request.path_params['id']
    id = int(id_string)

    # 模拟获取预签名 URL
    example_image_url = 'https://example.com/Snipaste_2025-05-09_15-45-43.png'

    mock_data: CombineInfoResponse = {
        'menu': {
            'id': 1,
            'name': '测试菜单',
            'image': example_image_url,
        },
        'categories': [
            {'name': '主食'},
            {'name': '汤类'},
            {'name': '甜点'},
            {'name': '其他'}
        ],
        'dishes': [
            {'name': '红烧肉', 'image': example_image_url, 'categoryName': '主食'},
            {'name': '番茄蛋汤', 'image': example_image_url, 'categoryName': '汤类'},
            {'name': '提拉米苏', 'image': example_image_url, 'categoryName': '甜点'}
        ]
    }

    return mock_data
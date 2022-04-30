from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# 创建数据模型
class Item(BaseModel):
    name: str = "lily"  # 可选参数，默认值为lily
    description: Optional[str] = None  # 可选参数，默认值为空值
    price: str  # 必选参数
    tax: Optional[float] = None


@app.post("/items/")
# 声明item为Item类型的参数
def create_item(item: Item):
    return item
#
@app.get("/items/")
# # 声明item为Item类型的参数
def create_item(item: Item):
    return item
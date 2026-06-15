import aiohttp
import logging
from bot.config import settings

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    elif response.status == 204:
                        return True
                    else:
                        try:
                            err_data = await response.json()
                            logger.error(f"Error {response.status} from {path}: {err_data}")
                            return {"error": True, "status": response.status, "detail": err_data}
                        except Exception:
                            err_text = await response.text()
                            logger.error(f"Error {response.status} from {path}: {err_text}")
                            return {"error": True, "status": response.status, "detail": err_text}
            except Exception as e:
                logger.exception(f"HTTP request failed: {url}")
                return {"error": True, "detail": str(e)}

    async def register_client(self, telegram_id: int, username: str, first_name: str, phone: str = None, language: str = None):
        payload = {
            "telegram_id": telegram_id,
            "username": username or "",
            "first_name": first_name,
            "phone": phone or ""
        }
        if language:
            payload["language"] = language
        return await self._request("POST", "/api/clients/register/", json=payload)

    async def get_settings(self):
        return await self._request("GET", "/api/settings/")

    async def get_categories(self):
        return await self._request("GET", "/api/categories/")

    async def get_products(self, category_id: int = None):
        params = {}
        if category_id:
            params["category_id"] = category_id
        return await self._request("GET", "/api/products/", params=params)

    async def get_product_detail(self, product_id: int):
        return await self._request("GET", f"/api/products/{product_id}/")

    async def get_print_positions(self):
        return await self._request("GET", "/api/print-positions/")

    async def get_cart(self, telegram_id: int):
        return await self._request("GET", "/api/cart/", params={"telegram_id": telegram_id})

    async def add_to_cart(self, telegram_id: int, product_id: int, size_id: int, color_id: int, 
                          print_position_id: int, quantity: int, design_file_bytes: bytes, 
                          filename: str, design_file_2_bytes: bytes = None, filename_2: str = None,
                          comment: str = ""):
        data = aiohttp.FormData()
        data.add_field("telegram_id", str(telegram_id))
        data.add_field("product", str(product_id))
        data.add_field("size", str(size_id))
        data.add_field("color", str(color_id))
        data.add_field("print_position", str(print_position_id))
        data.add_field("quantity", str(quantity))
        data.add_field("comment", comment)
        data.add_field("design_file", design_file_bytes, filename=filename)
        if design_file_2_bytes:
            data.add_field("design_file_2", design_file_2_bytes, filename=filename_2)
        
        return await self._request("POST", "/api/cart/add/", data=data)

    async def update_cart_item(self, item_id: int, quantity: int):
        payload = {
            "item_id": item_id,
            "quantity": quantity
        }
        return await self._request("POST", "/api/cart/update/", json=payload)

    async def delete_cart_item(self, item_id: int):
        return await self._request("DELETE", f"/api/cart/items/{item_id}/")

    async def clear_cart(self, telegram_id: int):
        payload = {"telegram_id": telegram_id}
        return await self._request("POST", "/api/cart/clear/", json=payload)

    async def get_payment_methods(self):
        return await self._request("GET", "/api/payment-methods/")

    async def checkout(self, telegram_id: int, full_name: str, phone: str, address: str, city: str):
        payload = {
            "telegram_id": telegram_id,
            "full_name": full_name,
            "phone": phone,
            "address": address,
            "city": city
        }
        return await self._request("POST", "/api/orders/checkout/", json=payload)

    async def get_orders(self, telegram_id: int):
        return await self._request("GET", "/api/orders/", params={"telegram_id": telegram_id})

    async def get_order_detail(self, order_id: int):
        return await self._request("GET", f"/api/orders/{order_id}/")

    async def upload_receipt(self, order_id: int, receipt_bytes: bytes, filename: str):
        data = aiohttp.FormData()
        data.add_field("image", receipt_bytes, filename=filename)
        return await self._request("POST", f"/api/orders/{order_id}/upload-receipt/", data=data)

    async def cancel_order(self, order_id: int):
        return await self._request("POST", f"/api/orders/{order_id}/cancel/")

    async def verify_receipt(self, receipt_id: int, action: str, token: str, comment: str = None):
        payload = {
            "action": action,
            "token": token
        }
        if comment:
            payload["comment"] = comment
        return await self._request("POST", f"/api/receipts/{receipt_id}/verify/", json=payload)

    async def get_manager_stats(self, telegram_id: int):
        return await self._request("GET", "/api/manager/stats/", params={"telegram_id": telegram_id})

    async def submit_other_services(self, telegram_id: int, comment: str, phone: str):
        payload = {
            "telegram_id": telegram_id,
            "comment": comment,
            "phone": phone
        }
        return await self._request("POST", "/api/orders/other-services/", json=payload)

    async def get_portfolio(self):
        return await self._request("GET", "/api/portfolio/")

api_client = APIClient(settings.backend_url)

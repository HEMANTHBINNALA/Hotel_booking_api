from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# -----------------------------
# DATA
# -----------------------------
rooms = [
    {"id": 1, "room_number": "101", "type": "Single", "price_per_night": 1000, "floor": 1, "is_available": True},
    {"id": 2, "room_number": "102", "type": "Double", "price_per_night": 1500, "floor": 1, "is_available": True},
    {"id": 3, "room_number": "201", "type": "Suite", "price_per_night": 3000, "floor": 2, "is_available": True},
    {"id": 4, "room_number": "202", "type": "Deluxe", "price_per_night": 4000, "floor": 2, "is_available": False},
    {"id": 5, "room_number": "301", "type": "Single", "price_per_night": 1200, "floor": 3, "is_available": True},
    {"id": 6, "room_number": "302", "type": "Double", "price_per_night": 1800, "floor": 3, "is_available": True},
]

bookings = []
booking_counter = 1

# -----------------------------
# HELPERS
# -----------------------------
def find_room(room_id):
    for room in rooms:
        if room["id"] == room_id:
            return room
    return None

def calculate_stay_cost(price, nights, meal_plan, early_checkout=False):
    extra = 0
    if meal_plan == "breakfast":
        extra = 500
    elif meal_plan == "all-inclusive":
        extra = 1200

    total = (price + extra) * nights
    discount = 0

    if early_checkout:
        discount = total * 0.1
        total -= discount

    return total, discount

def filter_rooms_logic(type, max_price, floor, is_available):
    result = rooms

    if type is not None:
        result = [r for r in result if r["type"].lower() == type.lower()]

    if max_price is not None:
        result = [r for r in result if r["price_per_night"] <= max_price]

    if floor is not None:
        result = [r for r in result if r["floor"] == floor]

    if is_available is not None:
        result = [r for r in result if r["is_available"] == is_available]

    return result

# -----------------------------
# MODELS
# -----------------------------
class BookingRequest(BaseModel):
    guest_name: str = Field(min_length=2)
    room_id: int = Field(gt=0)
    nights: int = Field(gt=0, le=30)
    phone: str = Field(min_length=10)
    meal_plan: str = "none"
    early_checkout: bool = False

class NewRoom(BaseModel):
    room_number: str
    type: str
    price_per_night: int = Field(gt=0)
    floor: int = Field(gt=0)
    is_available: bool = True

# -----------------------------
# Q1
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Grand Stay Hotel"}

# -----------------------------
# Q2
# -----------------------------
@app.get("/rooms")
def get_rooms():
    return {
        "total": len(rooms),
        "available_count": sum(1 for r in rooms if r["is_available"]),
        "rooms": rooms
    }

# -----------------------------
# Q5 (FIXED ROUTE)
# -----------------------------
@app.get("/rooms/summary")
def summary():
    prices = [r["price_per_night"] for r in rooms]
    types = {}
    for r in rooms:
        types[r["type"]] = types.get(r["type"], 0) + 1

    return {
        "total": len(rooms),
        "available": sum(r["is_available"] for r in rooms),
        "occupied": sum(not r["is_available"] for r in rooms),
        "min_price": min(prices),
        "max_price": max(prices),
        "types": types
    }

# -----------------------------
# Q10 (FIXED ROUTE)
# -----------------------------
@app.get("/rooms/filter")
def filter_rooms(
    type: Optional[str] = None,
    max_price: Optional[int] = None,
    floor: Optional[int] = None,
    is_available: Optional[bool] = None
):
    data = filter_rooms_logic(type, max_price, floor, is_available)
    return {"count": len(data), "rooms": data}

# -----------------------------
# Q16 SEARCH
# -----------------------------
@app.get("/rooms/search")
def search_rooms(keyword: str):
    result = [
        r for r in rooms
        if keyword.lower() in r["room_number"] or keyword.lower() in r["type"].lower()
    ]
    return {"total_found": len(result), "rooms": result}

# -----------------------------
# Q17 SORT
# -----------------------------
@app.get("/rooms/sort")
def sort_rooms(sort_by: str = "price_per_night", order: str = "asc"):
    if sort_by not in ["price_per_night", "floor", "type"]:
        raise HTTPException(400, "Invalid sort_by")

    reverse = order == "desc"
    return sorted(rooms, key=lambda x: x[sort_by], reverse=reverse)

# -----------------------------
# Q18 PAGINATION
# -----------------------------
@app.get("/rooms/page")
def paginate_rooms(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    total = len(rooms)

    return {
        "page": page,
        "total_pages": math.ceil(total / limit),
        "rooms": rooms[start:start + limit]
    }

# -----------------------------
# Q20 COMBINED
# -----------------------------
@app.get("/rooms/browse")
def browse_rooms(
    keyword: Optional[str] = None,
    sort_by: str = "price_per_night",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    data = rooms

    if keyword:
        data = [r for r in data if keyword.lower() in r["type"].lower()]

    reverse = order == "desc"
    data = sorted(data, key=lambda x: x[sort_by], reverse=reverse)

    start = (page - 1) * limit
    return {
        "total": len(data),
        "page": page,
        "rooms": data[start:start + limit]
    }

# -----------------------------
# Q3 (DYNAMIC ROUTE - LAST)
# -----------------------------
@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")
    return room

# -----------------------------
# Q4
# -----------------------------
@app.get("/bookings")
def get_bookings():
    return {"total": len(bookings), "bookings": bookings}

# -----------------------------
# Q8 + Q9
# -----------------------------
@app.post("/bookings")
def create_booking(req: BookingRequest):
    global booking_counter

    room = find_room(req.room_id)
    if not room:
        raise HTTPException(404, "Room not found")

    if not room["is_available"]:
        raise HTTPException(400, "Room occupied")

    total, discount = calculate_stay_cost(
        room["price_per_night"], req.nights, req.meal_plan, req.early_checkout
    )

    room["is_available"] = False

    booking = {
        "booking_id": booking_counter,
        "guest": req.guest_name,
        "room": room,
        "nights": req.nights,
        "meal_plan": req.meal_plan,
        "total_cost": total,
        "discount": discount,
        "status": "confirmed"
    }

    bookings.append(booking)
    booking_counter += 1

    return booking

# -----------------------------
# Q11
# -----------------------------
@app.post("/rooms", status_code=201)
def add_room(room: NewRoom):
    for r in rooms:
        if r["room_number"] == room.room_number:
            raise HTTPException(400, "Duplicate room number")

    new = room.dict()
    new["id"] = len(rooms) + 1
    rooms.append(new)
    return new

# -----------------------------
# Q12
# -----------------------------
@app.put("/rooms/{room_id}")
def update_room(
    room_id: int,
    price_per_night: Optional[int] = None,
    is_available: Optional[bool] = None
):
    room = find_room(room_id)
    if not room:
        raise HTTPException(404, "Room not found")

    if price_per_night is not None:
        room["price_per_night"] = price_per_night

    if is_available is not None:
        room["is_available"] = is_available

    return room

# -----------------------------
# Q13
# -----------------------------
@app.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    room = find_room(room_id)

    if not room:
        raise HTTPException(404, "Room not found")

    if not room["is_available"]:
        raise HTTPException(400, "Room occupied")

    rooms.remove(room)
    return {"message": "Room deleted"}

# -----------------------------
# Q14
# -----------------------------
@app.post("/checkin/{booking_id}")
def checkin(booking_id: int):
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "checked_in"
            return b
    raise HTTPException(404, "Booking not found")

# -----------------------------
# Q15
# -----------------------------
@app.post("/checkout/{booking_id}")
def checkout(booking_id: int):
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "checked_out"
            b["room"]["is_available"] = True
            return b
    raise HTTPException(404, "Booking not found")

@app.get("/bookings/active")
def active_bookings():
    return [b for b in bookings if b["status"] in ["confirmed", "checked_in"]]

# -----------------------------
# Q19
# -----------------------------
@app.get("/bookings/search")
def search_bookings(name: str):
    return [b for b in bookings if name.lower() in b["guest"].lower()]
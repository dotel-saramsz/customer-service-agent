from pydantic import BaseModel
import random
import os
import json
from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class OrderDetails(BaseModel):
    order_id: str
    item: str
    price: float
    is_refundable: bool
    ordered_date: str
    order_status: OrderStatus


sample_orders = [
    OrderDetails(
        order_id="1234",
        is_refundable=False,
        ordered_date="2024-07-01",
        order_status=OrderStatus.PENDING,
        item="Laptop",
        price=1000.0,
    ),
    OrderDetails(
        order_id="5678",
        is_refundable=False,
        ordered_date="2024-09-10",
        order_status=OrderStatus.DELIVERED,
        item="Monitor",
        price=400.0,
    ),
    OrderDetails(
        order_id="1111",
        is_refundable=False,
        ordered_date="2024-09-01",
        order_status=OrderStatus.DELIVERED,
        item="Headphones",
        price=150.0,
    ),
    OrderDetails(
        order_id="2222",
        is_refundable=True,
        ordered_date="2024-06-01",
        order_status=OrderStatus.SHIPPED,
        item="Keyboard",
        price=100.0,
    ),
    OrderDetails(
        order_id="9999",
        is_refundable=True,
        ordered_date="2024-08-01",
        order_status=OrderStatus.SHIPPED,
        item="Mouse",
        price=50.0,
    ),
]


def get_order_details(order_id: str):
    # Search for the order in sample_orders list
    for order in sample_orders:
        if order.order_id == order_id:
            return order.model_dump()

    return {"error": "Order not found!"}


def raise_support_ticket(
    order_id: str, reason_for_escalation: str, email: str, phone: str | None = None
):
    # Generate a ticket id
    ticket_id = random.randint(10000, 99999)
    with open("app/tickets/ticket_{}.txt".format(ticket_id), "w") as f:
        f.write("Ticket ID: {}\n".format(ticket_id))
        f.write(f"Order ID: {order_id}\n")
        f.write(f"Reason for escalation: {reason_for_escalation}\n")
        f.write(f"Customer Email: {email}\n")
        if phone:
            f.write(f"Customer Phone: {phone}\n")

    return {
        "ticket_id": ticket_id,
        "message": "Ticket has been raised successfully! Our support team will get in touch with you shortly.",
    }


def issue_refund(order_id: str, reason_for_refund: str):
    # refund the order

    # Check if the order is refundable or not
    order = get_order_details(order_id)

    if order.get("error"):
        return order
    elif not order["is_refundable"]:
        return {"error": "This order is not refundable."}
    else:
        # Refund the order
        return {"message": f"Refund has been initiated for Order: {order_id}."}


tools_func_mapping = {
    "get_order_details": get_order_details,
    "raise_support_ticket": raise_support_ticket,
    "issue_refund": issue_refund,
}


def get_tool_specs():
    # Read all the json files in the tools/spec directory

    tools_specs = []
    spec_dir = "app/tools/specs"

    for filename in os.listdir(spec_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(spec_dir, filename)
            with open(filepath, "r") as file:
                spec = json.load(file)
                tools_specs.append({"type": "function", "function": spec})

    return tools_specs


tools_specs = get_tool_specs()

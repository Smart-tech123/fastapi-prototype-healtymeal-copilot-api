from fastapi import Request


class HttpUtil:
    @classmethod
    def get_remote_address(cls, request: Request) -> str:
        if not hasattr(request, "client") or not request.client:  # noqa: SIM108
            ip_address = "127.0.0.1"
        else:
            ip_address = request.client.host

        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()

        return ip_address

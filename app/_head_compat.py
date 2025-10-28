from fastapi import APIRouter, Response

router = APIRouter()

@router.head("/healthz")
def _healthz_head():
    # HEAD não precisa de corpo; só 200 OK
    return Response(status_code=200)

@router.head("/guide")
def _guide_head():
    # HEAD para checagem rápida (favoritos, monitor, etc.)
    return Response(status_code=200)

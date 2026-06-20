"""Evidence file storage tests."""

from app.storage.repo_files import DatabaseFileStore


async def test_database_file_store_round_trip():
    store = DatabaseFileStore()
    content = b"employee_id,basic_salary\nEMP-1,10000\n"

    file_id = await store.store(content, "payroll.csv", "text/csv")

    assert await store.exists(file_id)
    assert await store.retrieve(file_id) == content
    assert await store.delete(file_id)
    assert not await store.exists(file_id)

import pytest

from database.repository import (
    insert_telemetry,
    get_latest_entry,
    get_recent_entries,
    get_hostnames,
    row_to_stats,
)
from config import HOSTNAME

TEST_HOSTNAME = "test_integracion"


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Limpia datos de test antes y después de cada prueba."""
    import psycopg2
    import psycopg2.extras
    from config import DATABASE_URL

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM telemetry WHERE hostname = %s", (TEST_HOSTNAME,))
    conn.commit()
    cur.close()
    conn.close()
    yield
    # Limpiar después
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM telemetry WHERE hostname = %s", (TEST_HOSTNAME,))
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture
def sample_system():
    return {
        "cpu_temp": 45.5,
        "ram": {
            "total": 17179869184,
            "used": 8589934592,
            "percent": 50.0,
        },
        "uptime_seconds": 3661.0,
    }


@pytest.fixture
def sample_gpu():
    return {
        "name": "Test GPU",
        "temperature": 65.0,
        "memory_total": 12884901888,
        "memory_used": 4294967296,
        "memory_percent": 33.3,
        "gpu_util": 45.0,
    }


class TestInsertAndRetrieve:
    def test_insert_and_get_latest(self, sample_system, sample_gpu):
        insert_telemetry(sample_system, sample_gpu, TEST_HOSTNAME)

        entry = get_latest_entry(TEST_HOSTNAME)
        assert entry is not None
        assert entry["hostname"] == TEST_HOSTNAME
        assert entry["cpu_temp"] == 45.5
        assert entry["gpu_name"] == "Test GPU"
        assert entry["gpu_temp"] == 65.0
        assert entry["uptime_seconds"] == 3661

    def test_insert_multiple_and_get_recent(self, sample_system, sample_gpu):
        for i in range(3):
            insert_telemetry(sample_system, sample_gpu, TEST_HOSTNAME)

        entries = get_recent_entries(3, hostname=TEST_HOSTNAME)
        assert len(entries) == 3
        for e in entries:
            assert e["hostname"] == TEST_HOSTNAME

    def test_get_recent_respects_limit(self, sample_system, sample_gpu):
        for i in range(5):
            insert_telemetry(sample_system, sample_gpu, TEST_HOSTNAME)

        entries = get_recent_entries(2, hostname=TEST_HOSTNAME)
        assert len(entries) == 2

    def test_get_latest_nonexistent_hostname(self):
        entry = get_latest_entry("hostname_inexistente_xyz")
        assert entry is None


class TestGetHostnames:
    def test_includes_test_hostname(self, sample_system, sample_gpu):
        insert_telemetry(sample_system, sample_gpu, TEST_HOSTNAME)

        hostnames = get_hostnames()
        assert TEST_HOSTNAME in hostnames

    def test_persistent_hostnames_remain(self):
        """Verifica que los hostnames reales (servidor) no fueron borrados."""
        hostnames = get_hostnames()
        assert HOSTNAME in hostnames

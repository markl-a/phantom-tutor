from phantom_tutor.cli import main
from phantom_tutor import memory


def test_design_grades_answer_via_stub_llm_and_records(tmp_path, capsys):
    ans = tmp_path / "ans.txt"
    ans.write_text("ingestion + chunking, embeddings + retrieval + rerank, serving latency, eval", encoding="utf-8")
    rc = main(["design", "--id", "d-rag", "--answer", str(ans)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "score=" in out and "FEEDBACK" in out.upper()
    assert "rag-system" in memory.load_store()

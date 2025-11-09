"""ChromaDB 내용 확인 스크립트"""
import chromadb
from chromadb.config import Settings
from rich.console import Console
from rich.table import Table

console = Console()

# ChromaDB 연결
client = chromadb.PersistentClient(
    path="./data/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

try:
    collection = client.get_collection(name="resumes")

    # 전체 데이터 조회
    results = collection.get()

    total_count = len(results['ids'])

    console.print("\n[bold green]ChromaDB 'resumes' 컬렉션 현황[/bold green]")
    console.print(f"총 저장된 이력서 수: [bold]{total_count}[/bold]개\n")

    if total_count > 0:
        # 테이블 생성
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("ID", width=30)
        table.add_column("파일명", width=35)
        table.add_column("문서 길이", justify="right", width=12)

        for i, (id_, metadata, doc) in enumerate(zip(
            results['ids'],
            results['metadatas'],
            results['documents']
        ), 1):
            filename = metadata.get('filename', 'N/A') if metadata else 'N/A'
            doc_length = f"{len(doc):,} chars" if doc else "N/A"
            table.add_row(
                str(i),
                id_,
                filename,
                doc_length
            )

        console.print(table)

        # 파일명별 통계
        console.print("\n[bold cyan]파일명별 통계:[/bold cyan]")
        filenames = [m.get('filename', 'Unknown') if m else 'Unknown'
                     for m in results['metadatas']]
        filename_counts = {}
        for fn in filenames:
            filename_counts[fn] = filename_counts.get(fn, 0) + 1

        # 중복이 있는 경우 경고
        duplicates = {k: v for k, v in filename_counts.items() if v > 1}
        if duplicates:
            console.print("\n[bold red]⚠️  중복된 파일 발견![/bold red]")
            for filename, count in duplicates.items():
                console.print(f"  - {filename}: [red]{count}개[/red]")
        else:
            console.print("[green]✓ 중복 없음[/green]")

    else:
        console.print("[yellow]저장된 이력서가 없습니다.[/yellow]")

except Exception as e:
    console.print(f"[bold red]오류 발생:[/bold red] {e}")
    console.print("\n[yellow]'resumes' 컬렉션이 아직 생성되지 않았을 수 있습니다.[/yellow]")

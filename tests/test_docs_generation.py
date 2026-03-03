from pathlib import Path

from docs.scripts.generate_trait_docs import main


def test_generate_trait_docs_creates_files():
    main()
    traits_dir = Path("docs/traits")
    assert (traits_dir / "space_grid.md").exists()
    assert (traits_dir / "time_forecast.md").exists()
    assert (traits_dir / "uncertainty_quantile.md").exists()

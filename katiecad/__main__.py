"""Start with:  python -m katiecad"""
from katiecad.ui.kt import oberflaeche_waehlen
oberflaeche_waehlen()            # Kivy (default) or Tk (KATIECAD_UI=tk)
from katiecad.ui.app import main  # noqa: E402

if __name__ == "__main__":
    main()

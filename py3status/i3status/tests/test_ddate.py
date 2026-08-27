"""Tests for the ddate i3status-compatible module."""


def test_ddate_normal_day():
    from datetime import date

    import py3status.i3status.modules.ddate as ddate_module

    discordian_date = ddate_module.Py3status._discordian_date

    # 2024-01-01: not a leap-year edge case, season_day=0 -> Chaos, Sweetmorn
    dt = discordian_date(date(2024, 1, 1))

    assert dt["st_tibs_day"] is False
    assert dt["season"] == 0
    assert dt["week_day"] == 0
    assert dt["season_day"] == 0
    assert dt["year"] == 3190
    assert dt["holiday"] is None


def test_ddate_st_tibs_day():
    from datetime import date

    import py3status.i3status.modules.ddate as ddate_module

    discordian_date = ddate_module.Py3status._discordian_date

    dt = discordian_date(date(2024, 2, 29))

    assert dt["st_tibs_day"] is True
    assert dt["season"] is None


def test_ddate_holiday():
    from datetime import date

    import py3status.i3status.modules.ddate as ddate_module

    discordian_date = ddate_module.Py3status._discordian_date

    # season_day=4 (5th day of the season) is Mungday in the Chaos season
    dt = discordian_date(date(2024, 1, 5))

    assert dt["season_day"] == 4
    assert dt["holiday"] == "Mungday"


def test_ddate_ordinal_suffix_11_12_13_are_all_th():
    import py3status.i3status.modules.ddate as ddate_module

    _ordinal_suffix = ddate_module.Py3status._ordinal_suffix

    assert _ordinal_suffix(11) == "th"
    assert _ordinal_suffix(12) == "th"
    assert _ordinal_suffix(13) == "th"
    assert _ordinal_suffix(1) == "st"
    assert _ordinal_suffix(2) == "nd"
    assert _ordinal_suffix(3) == "rd"
    assert _ordinal_suffix(4) == "th"
    assert _ordinal_suffix(21) == "st"


def test_ddate_full_render_normal_day(make_module, monkeypatch):
    from datetime import date

    import py3status.i3status.modules.ddate as ddate_module

    DDate = ddate_module.Py3status

    monkeypatch.setattr(
        ddate_module, "date", type("D", (), {"today": staticmethod(lambda: date(2024, 1, 1))})
    )
    module = make_module(DDate)
    module.post_config_hook()

    result = module.ddate()

    assert result["full_text"] == "SM, Chs 1, 3190 - "


def test_ddate_tibs_day_replaces_whole_block(make_module, monkeypatch):
    from datetime import date

    import py3status.i3status.modules.ddate as ddate_module

    DDate = ddate_module.Py3status

    monkeypatch.setattr(
        ddate_module, "date", type("D", (), {"today": staticmethod(lambda: date(2024, 2, 29))})
    )
    module = make_module(DDate)
    module.post_config_hook()

    result = module.ddate()

    assert result["full_text"].startswith("St. Tib's Day, 3190")

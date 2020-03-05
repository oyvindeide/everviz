import os
import time
import dash
from everviz.plugins.crossplot.layout.crossplot_layout import (
    get_sidebar_layout,
    _get_dropdown,
    _get_radio,
)
import pytest
import dash_html_components as html
import pandas as pd
import everviz
from everviz.plugins import Crossplot
from PIL import Image


@pytest.mark.parametrize(
    "test_input,expected",
    [(["dropdown_val"], "dropdown_val"), (["1", "2"], "1"), (["1", "2"], "2")],
)
def test_crossplot_layout_dropdown(dash_duo, test_input, expected):
    app = dash.Dash(__name__)
    item_id = "id"
    layout = _get_dropdown(item_id=item_id, options=test_input)
    app.layout = html.Div(layout)
    dash_duo.start_server(app)

    dash_duo.select_dcc_dropdown("#{}".format(item_id), expected)
    assert dash_duo.find_element("#{}".format(item_id)).text.split()[0] == expected


@pytest.mark.parametrize(
    "valid_options", [[("OPT_1", "nr_1"), ("OPT_2", "nr_2")], ["OPT_1", "OPT_2"]]
)
@pytest.mark.parametrize("expected, placement", [("OPT_1", 1), ("OPT_2", 2)])
def test_crossplot_layout_radio(dash_duo, expected, placement, valid_options):

    app = dash.Dash(__name__)
    layout = _get_radio("radio_id", options=valid_options)
    app.layout = html.Div(layout)
    dash_duo.start_server(app)

    text = dash_duo.find_element(
        "#{} label:nth-child({})".format("radio_id", placement)
    ).text
    assert text == expected


def test_get_sidebar_layout(monkeypatch, mocker):
    radio_mock = mocker.Mock(return_value=[])
    dropdown_mock = mocker.Mock(return_value=[])
    monkeypatch.setattr(
        everviz.plugins.crossplot.layout.crossplot_layout, "_get_radio", radio_mock
    )
    monkeypatch.setattr(
        everviz.plugins.crossplot.layout.crossplot_layout,
        "_get_dropdown",
        dropdown_mock,
    )

    get_sidebar_layout(
        [("radio", {"item_id": "radio_id"}), ("dropdown", {"item_id": "dropdown_id"})]
    )

    radio_mock.assert_called_once_with(item_id="radio_id")
    dropdown_mock.assert_called_once_with(item_id="dropdown_id")


def test_crossplot_layout(dash_duo, monkeypatch, mocker, tmpdir, assert_equal_images):
    app = dash.Dash(__name__)
    mock_data = pd.DataFrame(data=[[1, 2, 3]], columns=["a", "b", "c"])
    monkeypatch.setattr(
        everviz.plugins.crossplot.crossplot,
        "get_data",
        mocker.Mock(return_value=mock_data),
    )
    monkeypatch.setattr(
        everviz.plugins.crossplot.crossplot.Crossplot, "set_callbacks", mocker.Mock()
    )
    plugin = Crossplot(mocker.Mock(), "data_path")
    layout = plugin.layout
    app.layout = layout
    dash_duo.start_server(app)

    _REFERENCE_IMAGES = {
        (1024, 768): "crossplot_layout_headless.png",
        (1016, 635): "crossplot_layout.png",
    }

    dash_duo.driver.set_window_size(1024, 768)
    with tmpdir.as_cwd():
        # Graph can be slow to load, so we need to ensure it has loaded.
        time.sleep(1)
        dash_duo.driver.save_screenshot("example_snapshot.png")
        snapshot = Image.open("example_snapshot.png")

    if not snapshot.size in _REFERENCE_IMAGES:
        pytest.skip("No reference image for layout size: {}".format(snapshot.size))

    reference_image = Image.open(
        os.path.join(
            everviz.__path__[0],
            "..",
            "test-data",
            "crossplot",
            _REFERENCE_IMAGES[snapshot.size],
        )
    )

    assert_equal_images(reference_image, snapshot, threshold=0.5)
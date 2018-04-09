$(function() {
    function toggle_visible_quarters_menu() {
	$("#visible_quarters_control").toggle();
    }
    $("#visible_quarters_label").click(toggle_visible_quarters_menu);

    function show_hide_quarter_column(checkbox) {
	var qtr = $(checkbox).data('quarter');
	$(".players th[data-quarter='" + qtr + "'], " +
	  ".players td[data-quarter='" + qtr + "']").toggle(checkbox.checked);
    }
    $("input.visibleQtrFlag").change(function () {
	show_hide_quarter_column(this);
    });

    /* Initialize status of control widgets */
    $("#visible_quarters_control").toggle(false);
    $("input.visibleQtrFlag").each(function () {
	show_hide_quarter_column(this);
    });
});

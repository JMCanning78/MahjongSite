$(function() {
	var ratingsTmpl;

	$.get("/static/mustache/ratings.mst", function(data) {
		ratingsTmpl = data;
		Mustache.parse(ratingsTmpl);
		getData();
	});

	var ratings;

	function getData() {
		$.getJSON("/ratingsdata",
			function(data) {
				ratings = data;
				$("#players").html(Mustache.render(ratingsTmpl, data));
			});
	}
});

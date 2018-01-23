$(function() {
	$("#submit").on("click", function() {
		$("#submit").attr("disabled", true);
		var prevText = $("#submit").text();
		$("#submit").text("Adding...");

		submitGame('/addgame',
			function() {
				$("#message").text("GAME ADDED")
			},
			undefined,
			function() {
				$("#submit").attr("disabled", false);
				$("#submit").text(prevText);
			});
	});
});

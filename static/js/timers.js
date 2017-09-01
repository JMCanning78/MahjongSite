$(function() {
	var timerTemplate;
	$.get("/static/mustache/timer.mst", function(data) {
		timerTemplate = data;
		Mustache.parse(timerTemplate);
	});

	function startTimer(id) {
		$.post("/timers/start", {"id":id}, function(data) {
			if(data.status !== 0)
				console.log(data);
			else
				getTimers();
		});
	}

	function getTimers() {
		$.getJSON("/timers.json", function(data) {
			$("#timers").html(Mustache.render(timerTemplate, data));
			$(".start").click(function() {
				startTimer($(this).parent().data("id"));
			});
			updateTimers();
		});
	}
	function updateTimers() {
		$(".timer").each(function(i, timer) {
			var time = $(timer).data("time");
			var duration = new Date($(timer).data("duration") * 60 * 1000);
			if(time === undefined)
				time = new Date().getTime() + duration;
			else
				time = new Date(time.replace(/ /g, "T"));
			var remaining = new Date(Math.max(time - new Date(), 0));
			$(timer).children(".remaining").text(remaining.toUTCString().split(" ")[4] + "/" + duration.toUTCString().split(" ")[4]);
		});
	}
	getTimers();
	window.setInterval(updateTimers, 1000);

	$("#clear").click(function() {
		$.post("/timers/clear", {}, function(data) {
			if (data.status !== 0)
				console.log(data);
			else
				getTimers();
		});
	});
	$("#add").click(function() {
		var data = {
			"name":$("#name").val(),
			"duration":$("#duration").val(),
		};
		$.post("/timers/add", data, function(data) {
			if (data.status !== 0)
				console.log(data);
			else {
				getTimers();
				$("#name").val("");
				$("#duration").val("");
			}
		}, 'json');
	});
	$("#start").click(function() {
		startTimer();
	});
	$("#reset").click(function() {
		startTimer("all");
	});
});

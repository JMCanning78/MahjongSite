function fuUp() {
	var fu = parseInt($("#fu").text(), 10);
	if(fu == 20)
		fu = 25;
	else if(fu == 25)
		fu = 30;
	else
		fu = fu + 10;
	$("#fu").text(fu);

	updateScore();
}

function fuDown() {
	var fu = parseInt($("#fu").text(), 10);
	if(fu == 30)
		fu = 25;
	else
		fu = Math.max(fu - 10, 20);
	$("#fu").text(fu);

	updateScore();
}

function hanUp() {
	var han = parseInt($("#han").text(), 10);
	$("#han").text(Math.max(han + 1, 1));

	updateScore();
}

function hanDown() {
	var han = parseInt($("#han").text(), 10);
	$("#han").text(Math.max(han - 1, 1));

	updateScore();
}

function dealer() {
	var dealer = $("#dealer").text() === "";
	$("#dealer").text(dealer?"✓":"");

	updateScore();
}

function honba() {
	var honba = parseInt($("#honba").text(), 10);
	$("#honba").text((honba + 1) % 7);

	updateScore();
}

function updateScore() {
	var han = parseInt($("#han").text(), 10);
	var fu = parseInt($("#fu").text(), 10);

	if(fu === 20 && han === 1) {
		$("#total").html("<br />");
		$("#parent").html("<br />");
		$("#child").html("<br />");
		return;
	}

	var dealer = $("#dealer").text() !== "";

	if(han < 3 || (han === 4 && fu < 40) || (han === 3 && fu < 70)) {
		var basicPoints = fu * Math.pow(2, 2 + han);

		var total = (dealer?6:4) * basicPoints;
		total = Math.ceil(total / 100) * 100;
	}
	else if((han === 4 && fu >= 40) || (han === 3 && fu >= 70) || han === 5) {
		var total = dealer?12000:8000;
	}
	else if(han >= 6 && han <= 7) {
		var total = dealer?18000:12000;
	}
	else if(han >= 8 && han <= 10) {
		var total = dealer?24000:16000;
	}
	else if(han >= 11 && han <= 12) {
		var total = dealer?36000:24000;
	}
	else if(han >= 13) {
		var total = dealer?48000:36000;
	}

	total += parseInt($("#honba").text(), 10) * 300;


	$("#total").html("Total: " + total + "<br />");

	if(dealer) {
		var child = Math.ceil(total / 3 / 100) * 100;
		$("#parent").html("Child: " + child + "<br />");
		$("#child").html("<br />");
	}
	else {
		var parent = Math.ceil(total / 2 / 100) * 100;
		var child = Math.ceil(parent / 2 / 100) * 100;

		$("#parent").html("Parent: " + parent + "<br />");
		$("#child").html("Child: " + child + "<br />");
	}
}

$(document).ready(function() {
	$("#fuUp").click(fuUp);
	$("#fuDown").click(fuDown);

	$("#hanUp").click(hanUp);
	$("#hanDown").click(hanDown);

	$("#dealer").click(dealer);

	$("#honba").click(honba);

	updateScore();
});

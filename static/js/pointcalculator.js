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


function tsumo() {
	var tsumo = $("#tsumo").text() === "";
	$("#tsumo").text(tsumo?"✓":"");

	updateScore();
}

function updateScore() {
	var han = parseInt($("#han").text(), 10);
	var fu = parseInt($("#fu").text(), 10);

	var dealer = $("#dealer").text() !== "";
	var tsumo = $("#tsumo").text() !== "";

	if((fu === 20 && han === 1) || (fu === 25 && (han < 2 + tsumo?1:0))) {
		$("#scores").html("");
		return;
	}


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
		var total = dealer?48000:32000;
	}


	var scores = "";

	if(dealer) {
		if(tsumo) {
			var child = Math.ceil(total / 3 / 100) * 100;
			scores += "Total: " + child * 3 + "<br />";
			scores += "Payment: " + child;
		}
		else {
			scores += "<br />Total: " + total;
		}
	}
	else {
		if(tsumo) {
			var parent = Math.ceil(total / 2 / 100) * 100;
			var child = Math.ceil(parent / 2 / 100) * 100;

			scores += "Total: " + (parent + child * 2) + "<br />";
			scores += "Parent: " + parent + "<br />";
			scores += "Child: " + child + "<br />";
		}
		else {
			scores += "<br />Total: " + total;
		}

	}

	$("#scores").html(scores);
}

$(document).ready(function() {
	$("#fuUp").click(fuUp);
	$("#fuDown").click(fuDown);

	$("#hanUp").click(hanUp);
	$("#hanDown").click(hanDown);

	$("#dealer").click(dealer);

	$("#tsumo").click(tsumo);

	updateScore();
});

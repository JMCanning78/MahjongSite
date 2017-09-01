function filter(list, predicate) {
    var out = [];
    if (arguments.length < 2) { predicate = function (x) {return x} };
    for (var j = 0; j < list.length; j++) {
        if (predicate(list[j])) { out.push(list[j]) };
    };
    return out;
};

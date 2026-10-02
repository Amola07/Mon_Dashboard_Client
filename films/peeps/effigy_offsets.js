import React from "react";
export var Effigy = function (_a) {
    var style = _a.style, body = _a.body, head = _a.head, face = _a.face, beard = _a.beard, mask = _a.mask, accessory = _a.accessory;
    return (React.createElement("svg", { style: style, xmlns: 'http://www.w3.org/2000/svg', viewBox: '184.21621621621625 210.7874999999999 940.2702702702704 1130.5875', overflow: 'visible', width: '940.2702702702704px', height: '1130.5875px' },
        React.createElement("g", { id: 'Bust' },
            React.createElement("g", { id: 'Body', transform: 'translate(147, 639) scale(1 1)' }, createBody(body)),
            createHead(body, React.createElement(React.Fragment, null,
                React.createElement("g", { id: 'Hair', transform: 'translate(342, 190) scale(1 1)' }, createHair(head)),
                React.createElement("g", { id: 'Face', transform: 'translate(531, 366) scale(1 1)' }, createFace(face)),
                React.createElement("g", { id: 'Beard', transform: 'translate(495, 518) scale(1 1)' }, createBeard(beard)),
                React.createElement("g", { id: 'Mask', transform: 'translate(400, 480) scale(1 1)' }),
                React.createElement("g", { id: 'Accessories', transform: 'translate(419, 421) scale(1 1)' }, createAccessory(accessory)))))));
};
var createHair = function (head) {
    var _a;
    if (!head) {
        return null;
    }
    var element = (_a = require("./head/".concat(head.type))) === null || _a === void 0 ? void 0 : _a.default;
    var reactElement = React.createElement(element, head.options);
    if (head.type === "Bald") {
        return React.createElement("g", { transform: 'translate(50 20)' }, reactElement);
    }
    if (head.type === "BangsTwo") {
        return React.createElement("g", { transform: 'translate(20 0)' }, reactElement);
    }
    if (head.type === "BantuKnots") {
        return React.createElement("g", { transform: 'translate(30 0)' }, reactElement);
    }
    if (head.type === "Bear") {
        return React.createElement("g", { transform: 'translate(20 0)' }, reactElement);
    }
    if (head.type === "Bun") {
        return React.createElement("g", { transform: 'translate(-20 -30)' }, reactElement);
    }
    if (head.type === "Beanie") {
        return React.createElement("g", { transform: 'translate(20 0)' }, reactElement);
    }
    if (head.type === "BunClip") {
        return React.createElement("g", { transform: 'translate(20 -70)' }, reactElement);
    }
    if (head.type === "BunKnots") {
        return React.createElement("g", { transform: 'translate(10 -30)' }, reactElement);
    }
    if (head.type === "BunTwo") {
        return React.createElement("g", { transform: 'translate(-50 -90)' }, reactElement);
    }
    if (head.type === "ColorMedium") {
        return React.createElement("g", { transform: 'translate(30 0)' }, reactElement);
    }
    if (head.type === "CornrowsLight") {
        return React.createElement("g", { transform: 'translate(-15 0)' }, reactElement);
    }
    if (head.type === "DreadsTwo") {
        return React.createElement("g", { transform: 'translate(0 -15)' }, reactElement);
    }
    if (head.type === "FlatTop") {
        return React.createElement("g", { transform: 'translate(50 0)' }, reactElement);
    }
    if (head.type === "FlatTopLong") {
        return React.createElement("g", { transform: 'translate(50 0)' }, reactElement);
    }
    if (head.type === "GrayShort") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "HatHip") {
        return React.createElement("g", { transform: 'translate(-30 0)' }, reactElement);
    }
    if (head.type === "Hijab") {
        return React.createElement("g", { transform: 'translate(50 20)' }, reactElement);
    }
    if (head.type === "LongAfro") {
        return React.createElement("g", { transform: 'translate(-100 -130)' }, reactElement);
    }
    if (head.type === "LongBangs") {
        return React.createElement("g", { transform: 'translate(-25 0)' }, reactElement);
    }
    if (head.type === "LongCurly") {
        return React.createElement("g", { transform: 'translate(-50 -40)' }, reactElement);
    }
    if (head.type === "LongHair") {
        return React.createElement("g", { transform: 'translate(-50 0)' }, reactElement);
    }
    if (head.type === "MediumBangs") {
        return React.createElement("g", { transform: 'translate(-50 0)' }, reactElement);
    }
    if (head.type === "MediumBangsColor") {
        return React.createElement("g", { transform: 'translate(-20 0)' }, reactElement);
    }
    if (head.type === "MediumBangsOne") {
        return React.createElement("g", { transform: 'translate(40 10)' }, reactElement);
    }
    if (head.type === "MediumOne") {
        return React.createElement("g", { transform: 'translate(40 10)' }, reactElement);
    }
    if (head.type === "MediumStraight") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "MediumTwo") {
        return React.createElement("g", { transform: 'translate(-20 0)' }, reactElement);
    }
    if (head.type === "Mohawk") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "MohawkKnots") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "NoHairThree") {
        return React.createElement("g", { transform: 'translate(30 0)' }, reactElement);
    }
    if (head.type === "NoHairTwo") {
        return React.createElement("g", { transform: 'translate(30 0)' }, reactElement);
    }
    if (head.type === "Pomp") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "Shaved") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "ShavedOne") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "ShavedThree") {
        return React.createElement("g", { transform: 'translate(10 -20)' }, reactElement);
    }
    if (head.type === "ShortFive") {
        return React.createElement("g", { transform: 'translate(40 -10)' }, reactElement);
    }
    if (head.type === "ShortFour") {
        return React.createElement("g", { transform: 'translate(40 -10)' }, reactElement);
    }
    if (head.type === "ShortOne") {
        return React.createElement("g", { transform: 'translate(40 -10)' }, reactElement);
    }
    if (head.type === "ShortThree") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "ShortTwo") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "Turban") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "Twists") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "TwistsTwo") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    if (head.type === "Wavy") {
        return React.createElement("g", { transform: 'translate(40 0)' }, reactElement);
    }
    return reactElement;
};
var createFace = function (face) {
    var _a;
    var element = (_a = require("./face/".concat(face.type))) === null || _a === void 0 ? void 0 : _a.default;
    var reactElement = React.createElement(element, face.options);
    return reactElement;
};
var createBody = function (body) {
    var _a;
    var element = (_a = require("./body/effigy/".concat(body.type))) === null || _a === void 0 ? void 0 : _a.default;
    var reactElement = React.createElement(element, body.options);
    return reactElement;
};
var createBeard = function (beard) {
    var _a;
    if (!beard) {
        return null;
    }
    var element = (_a = require("./beard/".concat(beard.type))) === null || _a === void 0 ? void 0 : _a.default;
    var reactElement = React.createElement(element, beard.options);
    if (beard.type === "FullColor") {
        return React.createElement("g", { transform: 'translate(0 -20) scale(0.94 0.97)' }, reactElement);
    }
    if (beard.type === "FullMax") {
        return React.createElement("g", { transform: 'translate(0 -20) scale(0.98 1)' }, reactElement);
    }
    if (beard.type === "FullMedium") {
        return React.createElement("g", { transform: 'translate(0 -10) scale(0.98 1)' }, reactElement);
    }
    if (beard.type === "MustacheBull") {
        return React.createElement("g", { transform: 'translate(0 -20)' }, reactElement);
    }
    if (beard.type === "MustacheEight") {
        return React.createElement("g", { transform: 'translate(-240 -75)' }, reactElement);
    }
    return reactElement;
};
var createAccessory = function (accessory) {
    var _a;
    if (!accessory) {
        return null;
    }
    var element = (_a = require("./accessory/".concat(accessory.type))) === null || _a === void 0 ? void 0 : _a.default;
    var reactElement = React.createElement(element, accessory.options);
    if (accessory.type === "Eyepatch") {
        return React.createElement("g", { transform: 'translate(0 -60)' }, reactElement);
    }
    if (accessory.type === "SunglassesTwo") {
        return React.createElement("g", { transform: 'translate(-10 0)' }, reactElement);
    }
    return reactElement;
};
var createHead = function (body, children) {
    var group = (React.createElement("g", { id: 'Head', transform: 'translate(0 0)' }, children));
    if (body.type === "Explaining") {
        return React.createElement("g", { transform: 'translate(0 30)' }, group);
    }
    if (body.type === "PointingUp") {
        return React.createElement("g", { transform: 'translate(0 30)' }, group);
    }
    if (body.type === "PolkadotJacket") {
        return React.createElement("g", { transform: 'translate(0 20)' }, group);
    }
    if (body.type === "Killer") {
        return React.createElement("g", { transform: 'translate(0 10)' }, group);
    }
    if (body.type === "StrippedPocketTee") {
        return React.createElement("g", { transform: 'translate(250 0)' }, group);
    }
    if (body.type === "Whatever") {
        return React.createElement("g", { transform: 'translate(90 0)' }, group);
    }
    return group;
};

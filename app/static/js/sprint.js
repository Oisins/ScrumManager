$(function () {
    // Datumsauswahl Plugin aktivieren, da FF keine native support hat
    $("input.date-input").datepicker({dateFormat: "dd.mm.yy"});
});
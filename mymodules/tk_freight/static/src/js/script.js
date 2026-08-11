$(document).ready(function () {
    $('.submit-form').on('click', function (event) {

        let operation = $('#operation').val()
        let source = $('#source').val()
        let transportData = $('.transport-data').val()
        let destination = $('#destination').val()
        let danger = $('#danger').is(":checked")
        let danger_info = $('#danger_info').val()
        let notes = $('#notes').val()
        let alertEle = $('#validation-error')

        alertEle.addClass('d-none')
        if (!operation) {
            event.preventDefault()
            alertEle.text('Please select type !')
            alertEle.removeClass('d-none')
        } else if ($('input[name="transport"]:checked').length == 0) {
            event.preventDefault()
            alertEle.text('Please select transport !')
            alertEle.removeClass('d-none')
        } else if (!source) {
            event.preventDefault()
            alertEle.text('Please enter source location !')
            alertEle.removeClass('d-none')
        } else if (!destination) {
            event.preventDefault()
            alertEle.text('Please enter destination location !')
            alertEle.removeClass('d-none')
        } else if (danger && !danger_info) {
            event.preventDefault()
            alertEle.text('Please enter dangerous goods info !')
            alertEle.removeClass('d-none')
        } else if (!notes) {
            event.preventDefault()
            alertEle.text('Please enter notes !')
            alertEle.removeClass('d-none')
        } else {
            $('#quoteRequestForm')[0].submit();
        }
    });

    $('#danger').on('click', function (event) {
        if ($(this).is(":checked")) {
            $('#danger_info_div').removeClass('d-none')
        } else {
            $('#danger_info_div').addClass('d-none')
        }
    })
})
function confirmModal(prompt, fn, arg1, arg2, arg3, arg4, arg5, arg6) {
    if (confirm(prompt)) {
        fn(arg1, arg2, arg3, arg4, arg5, arg6)
    }
}

function deleteBenefit(storeId){
    console.log(storeId + " delete")
    jQuery.ajax({
        url: '/benefits/'+storeId,
        type: 'DELETE',
        success: function(result) {
            location.reload()
        }
    });
}

function showBenefitType() {
    var typeInput= $("#type")
    if (typeInput.length>1) {
        typeInput = typeInput.find(":selected")
    }
    var selectedType = typeInput.val()

    var containers = $(".benefitType")
    containers.hide()
    containers.filter("#type"+selectedType).show()
}
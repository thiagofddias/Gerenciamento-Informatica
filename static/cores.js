document.addEventListener('DOMContentLoaded', function () {
    var elements = document.getElementsByClassName('menu');
    var logoElement = document.querySelector('.logo img');
    var botaoElements = document.querySelectorAll('.botao');
    var cabecalhoElements = document.querySelectorAll('.fixed-header th');
    var modais = document.querySelectorAll('.modal');
    var demaisButtonElements = document.querySelectorAll('.demaisbutton');
    var confirmarElements = document.querySelectorAll('.confirmar');
    var plantaEditElements = document.querySelectorAll('.planta_edit');
    var plantacolabs = document.querySelectorAll('.plantahist');
    var icones = document.querySelectorAll('label i');
    var fecharElements = document.querySelectorAll('#IconeFechar');
    var iconeLixo = document.querySelectorAll('#iconeLixo');

    function alterarCores() {
        var corFundo, corBorda, corHover;

        if (planta === "A") {
            corFundo = '#0a4338';
            corBorda = '#0a4338';
            corHover = '#096352';
            if (logoElement) {
                logoElement.src = "#";
            }
        }

        if (planta === "B") {
            corFundo = '#012269';
            corBorda = '#012269';
            corHover = '#03a5fc';
            if (logoElement) {
                logoElement.src = "#";
            }
        }
        else if (planta === "ALL") {
            corFundo = '#000000';
            corBorda = '#666669';
            corHover = '#03dffc';
            if (logoElement) {
                logoElement.src = "#";
            }

            plantaEditElements.forEach(function (plantaEditElement) {
                plantaEditElement.removeAttribute('hidden');
            });

            plantacolabs.forEach(function (plantacolab) {
                plantacolab.removeAttribute('hidden');
            });
        }

        for (var i = 0; i < elements.length; i++) {
            elements[i].style.backgroundColor = corFundo;
        }

        cabecalhoElements.forEach(function (cabecalhoElement) {
            cabecalhoElement.style.backgroundColor = corFundo;
        });

        modais.forEach(function (modal) {
            modal.style.borderColor = corBorda;
        });

        icones.forEach(function (icone) {
            icone.style.backgroundColor = corFundo;
            icone.style.color = '#fff';
        });


        fecharElements.forEach(function (fecharElement) {
            fecharElement.style.background = '#dfe3ed';
            fecharElement.style.color = 'red';
        });

        iconeLixo.forEach(function (iconeLixo) {
            iconeLixo.style.background = 'none';
        });


        botaoElements.forEach(function (botaoElement) {
            botaoElement.addEventListener('mouseover', function () {
                botaoElement.style.backgroundColor = corFundo;
                botaoElement.style.color = '#fff';
                botaoElement.style.borderColor = corBorda;
            });

            botaoElement.addEventListener('mouseout', function () {
                botaoElement.style.backgroundColor = '';
                botaoElement.style.color = '';
                botaoElement.style.borderColor = '';
            });
        });

        demaisButtonElements.forEach(function (demaisButtonElement) {
            demaisButtonElement.addEventListener('mouseover', function () {
                demaisButtonElement.style.backgroundColor = corHover;
                demaisButtonElement.style.color = '#fff';
            });

            demaisButtonElement.addEventListener('mouseout', function () {
                demaisButtonElement.style.backgroundColor = corFundo;
                demaisButtonElement.style.color = '#fff';
            });
        });


        confirmarElements.forEach(function (confirmarElement) {
            confirmarElement.addEventListener('mouseover', function () {
                confirmarElement.style.backgroundColor = corHover;
                confirmarElement.style.color = '#fff';
            });

            confirmarElement.addEventListener('mouseout', function () {
                confirmarElement.style.backgroundColor = corFundo;
                confirmarElement.style.color = '';
            });
        });

        var menuAHoverElements = document.querySelectorAll('.menu a:hover');

        menuAHoverElements.forEach(function (menuAHoverElement) {
            menuAHoverElement.addEventListener('mouseover', function () {
                menuAHoverElement.style.backgroundColor = corHover;
                menuAHoverElement.style.color = corHover;
            });

            menuAHoverElement.addEventListener('mouseout', function () {
                menuAHoverElement.style.backgroundColor = corHover;
                menuAHoverElement.style.color = 'corHover';
            });
        });
    }

    alterarCores();
});
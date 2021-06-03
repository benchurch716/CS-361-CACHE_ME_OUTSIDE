function updateSlide() {
  slides = Array.from(document.getElementsByClassName("slide"));
  slides.map(s => s.style.display = "none")
  slides[slideIndex].style.display = "inline";
}


function plusSlides() {
    slideIndex = (slideIndex + 1) % slides.length;
    updateSlide();
}


function minusSlides() {
    slideIndex = (slideIndex - 1) % slides.length;    
    if (slideIndex < 0) {
        slideIndex = slides.length - 1;
    }
    updateSlide();
}
  

var slideIndex = 0;
var slides;
window.onload = updateSlide;
/*!
* Start Bootstrap - Clean Blog v6.0.8 (https://startbootstrap.com/theme/clean-blog)
* Copyright 2013-2022 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-clean-blog/blob/master/LICENSE)
*/
window.addEventListener('DOMContentLoaded', () => {
    let scrollPos = 0;
    const mainNav = document.getElementById('mainNav');
    const headerHeight = mainNav.clientHeight;
    window.addEventListener('scroll', function() {
        const currentTop = document.body.getBoundingClientRect().top * -1;
        if ( currentTop < scrollPos) {
            // Scrolling Up
            if (currentTop > 0 && mainNav.classList.contains('is-fixed')) {
                mainNav.classList.add('is-visible');
            } else {
                console.log(123);
                mainNav.classList.remove('is-visible', 'is-fixed');
            }
        } else {
            // Scrolling Down
            mainNav.classList.remove(['is-visible']);
            if (currentTop > headerHeight && !mainNav.classList.contains('is-fixed')) {
                mainNav.classList.add('is-fixed');
            }
        }
        scrollPos = currentTop;
    });
})
function removeFlash(message) {
  const element = document.getElementById('div_flash');
  element.remove();
}
function getBotResponse() {
event.preventDefault();
          var userMessage = $("#chatbot-input").val();
          const el = document.getElementById('chatbot-body');

          $("#chatbot-input").val("");
          $("#chatbot-body").append(`
            <div class="small p-2 ms-3 mb-1 rounded-3" style="background-color: blue;">
              <p><b>User:</b> ${userMessage}</p>
            </div>
          `);
          if (el) {
                          el.scrollTop = el.scrollHeight;
                   }
          $.ajax({
            url: "/chatbot",
            method: "POST",
            data: {message: userMessage},
            success: function(response) {
              $("#chatbot-body").append(`
                <div class="small p-2 ms-3 mb-1 rounded-3" style="background-color: green;">
                  <p><b>Bot:</b> ${response}</p>
                </div>
              `);
              if (el) {
                          el.scrollTop = el.scrollHeight;
                      }
            }
          });
}

$("#chatbot-input").keypress(function(e) {
					if(e.which == 13) {
						getBotResponse();
					}
				});




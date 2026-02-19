$(document).ready(function() {
    function toggleInputElements(disabled) {
        $('input[name=message]').prop('disabled', disabled);
        $('.send-button').prop('disabled', disabled);
    }

    function adjustInputHeight() {
        var input = $('input[name=message]')[0];
        input.style.height = 'auto'; // Reset height
        input.style.height = (input.scrollHeight) + 'px'; // Set height based on content
    }

    function sendMessage() {
        var userMessage = $('input[name=message]').val().trim();

        if (userMessage === '') {
            return;
        }

        toggleInputElements(true);

        $('.chat-messages').append('<div class="message-container"><div class="user-message">' + userMessage + '</div></div>');

        $('input[name=message]').val('');
        adjustInputHeight();
        $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);

        var sentiment = $('input[name=sentiment]').val(); // Get the sentiment value

        console.log('Sending message to server:', userMessage, sentiment); // Log message to be sent

        $.post("/chat", {
            prompt: userMessage,
            sentiment: sentiment // Pass sentiment to the server
        }, function(response) {
            console.log('Received response from server:', response); // Log received response

            // Display the bot's response
            $('.chat-messages').append('<div class="message-container"><div class="chatbot-profile"><img src="static/EnSys_prof.png" alt="EnSys Profile Image"></div><div class="message">' + formatMenu(response.response) + '</div></div>');

            // Display the suggestions as buttons
            $('.suggestions-container').empty();
            var suggestionsHtml = '<div class="suggestion-buttons">';
            response.suggestions.forEach(function(suggestion) {
                suggestionsHtml += '<button class="suggestion-button">' + suggestion + '</button>';
            });
            suggestionsHtml += '</div>';
            $('.suggestions-container').append(suggestionsHtml);

            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);
            toggleInputElements(false);

            // Add click event to suggestions
            $('.suggestion-button').click(function() {
                var suggestionText = $(this).text();
                $('input[name=message]').val(suggestionText);
            });
        }).fail(function() {
            $('.chat-messages').append('<div class="message-container"><div class="message">Something went wrong</div></div>');
            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);
            toggleInputElements(false);
        });
    }

    function formatMenu(response) {
        var formattedResponse = '';
        var lines = response.split('\n');
        lines.forEach(function(line) {
            if (line.includes(':')) {
                formattedResponse += '<strong>' + line + '</strong><br>';
            } else {
                formattedResponse += line + '<br>';
            }
        });
        return formattedResponse;
    }

    function initializeSuggestions() {
        var sentiment = $('input[name=sentiment]').val(); // Get the sentiment value

        $.post("/chat", {
            prompt: '',
            sentiment: sentiment // Pass sentiment to the server
        }, function(response) {
            console.log('Received initial suggestions from server:', response);

            // Display the suggestions as buttons
            $('.suggestions-container').empty();
            var suggestionsHtml = '<div class="suggestion-buttons">';
            response.suggestions.forEach(function(suggestion) {
                suggestionsHtml += '<button class="suggestion-button">' + suggestion + '</button>';
            });
            suggestionsHtml += '</div>';
            $('.suggestions-container').append(suggestionsHtml);

            // Add click event to suggestions
            $('.suggestion-button').click(function() {
                var suggestionText = $(this).text();
                $('input[name=message]').val(suggestionText);
            });
        }).fail(function() {
            console.log('Failed to fetch initial suggestions');
        });

    }

    $('.send-button').click(function() {
        sendMessage();
    });

    $('input[name=message]').keypress(function(event) {
        if (event.which === 13) { // Enter key pressed
            sendMessage();
            return false; // Prevent the default form submission
        }
    });

    adjustInputHeight();
    initializeSuggestions(); // Fetch and display suggestions at the start
});

$('input[name=message]').on('input', function() {
    var userInput = $(this).val().trim().toLowerCase();
    if (userInput === 'menu') {
        $.post("/chat", {
            prompt: 'MENU'
        }, function(response) {
            var formattedMenu = formatMenu(response);
            $('.chat-messages').append('<div class="message-container"><div class="message">' + formattedMenu + '</div></div>');
            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);
        });
        $('input[name=message]').val('');
    }
});

function endChat() {
    $.post("/chat", {
        prompt: 'END CHAT'
    }, function(response) {
        if (response === 'END CHAT') {
            window.location.href = '/rate';
        }
    });
}

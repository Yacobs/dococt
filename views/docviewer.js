var intervalCheckForPDF;
var pdfFilesize;
var pdfCheckRunning;

$(document).ready(function ()
{
	pdfFilesize = 0;
	pdfCheckRunning = false;
	intervalCheckForPDF = setInterval(checkForConvertedPDF, 1500);
});

function checkForConvertedPDF()
{
	if (pdfCheckRunning) return;	// don't keep slamming the server
	pdfCheckRunning = true;
	
	$.ajax({
		type: 'HEAD',
		url: txtFile + '.txt',
		success: function(data, textStatus, jqXHR){
			// found it
			pdfCheckRunning = false;
			
			if (pdfFilesize == jqXHR.getResponseHeader('Content-Length'))
			{
				clearInterval(intervalCheckForPDF);
			
				$('#processingDiv').addClass('hidden');
				$('#doneDiv').removeClass('hidden');
			}
			else pdfFilesize = jqXHR.getResponseHeader('Content-Length');
		},
		error: function(jqXHR, textStatus, errorThrown){
			pdfCheckRunning = false;
		}
	});
}
var intervalCheckForPDF;
var pdfFilesize;
var pdfCheckRunning;

$(document).ready(function ()
{
	if (status == 'converting')
	{
		pdfFilesize = -1000;
		pdfCheckRunning = false;
		intervalCheckForPDF = setInterval(checkForConvertedPDF, 1500);
	}
});

function docViewerShow(i, j, k)
{
	$('.docViewerText').addClass('hidden')
	$('#docViewerText_' + i + '_' + j + '_' + k).removeClass('hidden')
}

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
				$('#cleaningDiv').removeClass('hidden');
				
				cleanUpConvertedPDF();
			}
			else pdfFilesize = jqXHR.getResponseHeader('Content-Length');
		},
		error: function(jqXHR, textStatus, errorThrown){
			pdfCheckRunning = false;
		}
	});
}

function cleanUpConvertedPDF()
{
	$.post('/doccleanup', { filename: txtFile }, function( data ) 
	{
		if (data == 'Done')
		{
			window.location.replace("/docviewer?status=done&file=" + txtFile);
		}
		else alert( "Error on clean-up..." );
	})
	.fail(function() 
	{
		alert( "Error on clean-up..." );
	})
	.always(function() 
	{
		// yyyy
	});
}

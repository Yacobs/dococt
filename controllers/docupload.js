/**
 * POST /
 * Upload a document.
 */
exports.docUpload = function(req, res) {
	/*
	if(done==true)
	{
		console.log(req.files);
		res.end("File uploaded.");
	}
	*/
	
	console.log(req.header);
	console.log(req.file);
	
	if (typeof req.file == 'undefined') res.redirect('/');
	else res.redirect('docviewer?file=' + req.file.filename);
};

exports.docViewer = function(req, res) 
{
	res.render('docviewer', {
		title: 'Document Viewer'
	});
}
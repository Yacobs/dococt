/**
 * POST /
 * Upload a document.
 */
exports.docUpload = function(req, res, next) {
	/*
	if(done==true)
	{
		console.log(req.files);
		res.end("File uploaded.");
	}
	*/
	console.log(req.file);
	res.end("Done.")
};
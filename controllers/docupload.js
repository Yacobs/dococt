/**
 * POST /
 * Upload a document.
 */
exports.docUpload = function(req, res) 
{
	console.log(req.header);
	console.log(req.file);
	
	if (typeof req.file == 'undefined') res.redirect('/');
	else 
	{
		var python = require('child_process').spawn(
		'python',
		['pdf2txt.py', '-o '+ req.file.filename + '.txt', req.file.filename ]
		);
		
		python.on('close', function(code){
			if (code !== 0) console.log('Failed');
			else console.log('Succeeded.');
		});
		
		res.redirect('docviewer?file=' + req.file.filename);
	}
};

exports.docViewer = function(req, res) 
{
	//if (typeof req.query.file == 'undefined') 
	//else 
	res.render('docviewer', { title: 'Document Viewer', file: req.query.file });
}
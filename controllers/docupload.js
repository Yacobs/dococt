/**
 * POST /
 * Upload a document.
 */
exports.docUpload = function(req, res) 
{
	//console.log(req.header);
	//console.log(req.file);
	
	if (typeof req.file == 'undefined') res.redirect('/');
	else res.redirect('docviewer?status=converting&file=' + req.file.filename);

	var python = require('child_process').spawn(
	'python',
	['pdf2txt.py', '-o', './uploads/' + req.file.filename + '.txt', './uploads/' + req.file.filename ]
	);
	
	python.stdout.on('data', function(data){ console.log('stdout: ' + data)  });
	python.stderr.on('data', function(data){ console.log('stderr: ' + data)  });
	
	python.on('close', function(code){
		if (code !== 0) console.log('PDF Conversion Failed:' + code);
		else console.log('PDF Conversion Succeeded.');
	});
};

exports.docCleanUp = function(req, res)
{
	//console.log(req.body);
	
	if (typeof req.body.filename == 'undefined') res.redirect('/');

	var python = require('child_process').spawn(
	'python',
	['page_remover.py', 
		'-i', './uploads/' + req.body.filename + '.txt', 
		'-o', './uploads/' + req.body.filename + '_clean.txt',
		'-s', 'indenture.json'
	]
	);
	
	python.stdout.on('data', function(data){ console.log('stdout: ' + data)  });
	python.stderr.on('data', function(data){ console.log('stderr: ' + data)  });
	
	python.on('close', function(code){
		if (code !== 0) 
		{
			console.log('Clean-Up Failed -- Exit Code: ' + code);
			res.send('Failed');
		}
		else 
		{
			console.log('Clean-Up Succeeded.');
			res.send('Done');
		}
	});
}

exports.docViewer = function(req, res) 
{
	res.render('docviewer', { title: 'Document Viewer', status: req.query.status, file: req.query.file });
}
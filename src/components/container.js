import React, {Component} from 'react';

class Container extends Component {

	render(){		
		return(
			<div>
				<table className="table table-light">
					<tbody>
						<tr>
							<td>{this.props.id}</td>
							<td>{this.props.name}</td>
							<td>{this.props.status}</td>
							<td>{this.props.image}</td>
							<td><button className="btn red">View</button></td>
						</tr>
					</tbody>
				</table>
			</div>
		);
	}
}

export default Container;
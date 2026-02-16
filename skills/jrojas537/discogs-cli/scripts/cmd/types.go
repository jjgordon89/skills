package cmd

// Shared types for Discogs API responses

type Artist struct {
	Name string `json:"name"`
}

type Image struct {
	Type        string `json:"type"`
	URI         string `json:"uri"`
	ResourceURL string `json:"resource_url"`
	URI150      string `json:"uri150"`
	Width       int    `json:"width"`
	Height      int    `json:"height"`
}

type Release struct {
	Title   string   `json:"title"`
	Artists []Artist `json:"artists"`
	Images  []Image  `json:"images"`
}

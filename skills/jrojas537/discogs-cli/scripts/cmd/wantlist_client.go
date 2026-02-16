package cmd

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"github.com/spf13/viper"
)

func wantlistRequest(method, url string, target interface{}) error {
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		return err
	}

	// This is a bit of a hack, but we need to get the header from the client
	// I'll look for a better way to do this later.
	// For now, I'll just re-create it.
	token := viper.GetString("token")
	req.Header.Add("User-Agent", "OpenClawDiscogsSkill/1.0")
	req.Header.Add("Authorization", "Discogs token="+token)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNoContent && resp.StatusCode != http.StatusCreated {
		return fmt.Errorf("API request failed with status: %s", resp.Status)
	}

	if target != nil {
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			return err
		}
		return json.Unmarshal(body, target)
	}

	return nil
}
